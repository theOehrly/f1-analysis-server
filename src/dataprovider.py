"""
:mod:`dbconnector` - Abstraction of Database Requests
=====================================================

This module provides an interface to the backend database.
"""

import pymongo
from lookuptables import driver_query
from datetime import datetime


class DataProvider:
    def __init__(self, address):
        """MongoDB wrapper class

        Should make database requests easier and make them look nicer.

        :param address: server address
        :type address: str
        """
        self._dbclient = pymongo.MongoClient(address)
        self._f1info_db = self._dbclient['F1Info']
        self._events = self._f1info_db['Events']
        self._sessions = self._f1info_db['Sessions']
        self._drivers = self._f1info_db['Drivers']

    def get_events_names(self, **kwargs):
        """ Return a list of event names and ids

        :return: List of events; one dict per event containing event id and name [{'id': ..., 'name': ...}, ]
        :param kwargs: optional; you can pass keyword arguments which are directly passed to pymongo's .find({filter_key=val})
        """
        return list(self._events.find(kwargs, {'_id': 0, 'id': 1, 'name': 1}))

    def get_sessions_names(self, **kwargs):
        """Return a list of session names and ids

        :return: List of sessions; one dict per session containing session id and name [{'id': ..., 'name': ...}, ]
        :param kwargs: optional; you can pass keyword arguments which are directly passed to pymongo's .find({filter_key=val})
        """
        return list(self._sessions.find(kwargs, {'_id': 0, 'id': 1, 'name': 1, 'date': 1, 'startTime': 1, 'endTime': 1}))

    def get_value_from_session(self, sessionid, key):
        """Key-value lookup for the provided session id and key

        :type sessionid: str
        :type key: str
        """
        filter_dict = {'_id': 0, key: 1}
        return self._sessions.find_one({'id': sessionid}, filter_dict)[key]

    def get_telemetry_data(self, options):
        """Return telemetry data for multiple drivers and laps.

        :param options: request options as specified in the API documentation for `Request Data (/data/telemetry)`
        """
        ret = list()

        ch_name = options['channel']
        sid = options['session']

        for driver in options['drivers']:
            driver_number = driver_query(by='Abb', value=driver, get='Number')

            if options['selectBy'] == 'fastest':
                timing_data = self.get_timing_data(sid, driver_number, lap='fastest')

            elif options['selectBy'] == 'time':
                # currently everything works in UTC; event local time might be preferred for later
                start = datetime.utcfromtimestamp(options['timeStartValue'] / 1000)
                end = datetime.utcfromtimestamp(options['timeEndValue'] / 1000)
                timing_data = self.get_timing_data(sid,
                                                   driver_number,
                                                   timerange=(start, end),
                                                   starts_in=bool(options['timeStartIn']),
                                                   ends_in=bool(options['timeEndIn']))

            elif options['selectBy'] == 'laps':
                timing_data = self.get_timing_data(sid, driver_number, lap=options['laps'])

            else:
                raise ValueError("Invalid value for 'selectBy': {}".format(options['selectBy']))

            for lap in timing_data:
                lap_id = lap['_id']  # list should always only have one item
                telemetry = self.get_lap_telemetry(sid, lap_id, filter_channels=(ch_name,))
                ret.append({'driver': driver, 'telemetry': telemetry, 'laptime': lap['LapTime'], 'lapnumber': lap['LapNumber']})

        return ret

    def get_time_range(self, session_id, carnumber, datatype, channel, starttime, endtime):
        """ Get a filtered range of data from a session

        :param session_id: the sessions unique id
        :param carnumber: the driver/car number
        :param datatype: one of the available datatypes, e.g. 'data' or 'position'
        :param channel: one of the available F1 Telemetry channel
        :param starttime: range start
        :param endtime: range end

        :type session_id: str
        :type carnumber: str
        :type datatype: str
        :type channel: str
        :type starttime: datetime or pandas.Timestamp
        :type endtime: datetime or pandas.Timestamp

        :return: PyMongo Cursor for the selected time range and for the selected car.
          Results are filtered so they only contain the time and the selected channel
        """
        session = self._dbclient[session_id]
        collection = session[carnumber + '-' + datatype]
        channel_filter = {'_id': 0, 'time': 1, channel: 1}
        return collection.find({'time': {'$gte': starttime, '$lt': endtime}}, channel_filter)

    def get_timing_data(self, session_id, drivernumber, lap=(), timerange=(), starts_in=True, ends_in=True):
        """Return timing data based on a variety of filter options.

        :param session_id: the sessions unique id
        :param drivernumber: the driver's number
        :param lap: (optional) which laps should be returned; can be a lap number, a list of lap numbers or the string "fastest"
        :param timerange: (optional) a tuple containing two timestamps (start, end)

        One of `lap` and `timerange` needs to be specified. But both may not be specified at the same time!

        :param starts_in: (optional, `with timerange only`) whether the laps needs to start in the specified time range (default: True)
        :param ends_in: (optional, `with timerange only`) whether the laps needs to end in the specified time range (default: True)

        `starts_in` and `ends_in` may not both be false!
        """
        assert not (lap and timerange), "Parameters Lap and Timerange are mutually exclusive"
        assert lap or timerange, "Either parameter Lap or Timerange needs to be specified"

        collection = self._dbclient[session_id]['timingdata']

        if lap:
            if lap == 'fastest':
                timing_data = list(collection.find({'DriverNumber': drivernumber}).sort('LapTime', 1).limit(1))
            elif isinstance(lap, (tuple, list)) and all(isinstance(itm, (int, float)) for itm in lap):
                timing_data = list(collection.find({'DriverNumber': drivernumber, 'LapNumber': {'$in': lap}}))
            elif isinstance(lap, (int, float)):
                timing_data = list(collection.find({'DriverNumber': drivernumber, 'LapNumber': lap}))
            else:
                raise ValueError("Invalid value for lap: {}".format(lap))

        else:
            start = timerange[0]
            end = timerange[1]

            if starts_in and ends_in:
                timing_data = list(collection.find({'$and': [{'LapStartDate': {'$gte': start}},
                                                             {'LapStartDate': {'$lte': end}},
                                                             {'LapEndDate': {'$gte': start}},
                                                             {'LapEndDate': {'$lte': end}},
                                                             {'DriverNumber': drivernumber}]}))
            elif starts_in:
                timing_data = list(collection.find({'$and': [{'LapStartDate': {'$gte': start}},
                                                   {'LapStartDate': {'$lte': end}},
                                                   {'DriverNumber': drivernumber}]}))
            elif ends_in:
                timing_data = list(collection.find({'$and': [{'LapEndDate': {'$gte': start}},
                                                   {'LapEndDate': {'$lte': end}},
                                                   {'DriverNumber': drivernumber}]}))
            else:
                raise ValueError("starts_in and ends_in can not both be false")

        return timing_data

    def get_lap_telemetry(self, session_id, lap_id, filter_channels=()):
        """Return one or multiple telemetry data channels for one lap.

        :param session_id: the sessions unique id
        :param lap_id: the laps numeric id
        :param filter_channels: (optional) a list of channel names

        :type session_id: str
        :type lap_id: int
        :type filter_channels: list or tuple
        """
        channels = {'_id': 0, 'SessionTime': 1}
        if filter_channels:
            for name in filter_channels:
                channels[name] = 1

        telemetry = list(self._dbclient[session_id]['telemetry'].find({'LapId': lap_id}, channels))
        return telemetry

    def insert_many(self, db_name, collection_name, data):
        """Insert multiple documents into a collection.

        Wraps pymongo's insert_many()

        :type db_name: str
        :type collection_name: str
        :type data: list or tuple or pandas.DataFrame
        """
        self._dbclient[db_name][collection_name].insert_many(data)
