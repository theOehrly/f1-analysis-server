import pymongo


class DatabaseConnector:
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
        return list(self._sessions.find(kwargs, {'_id': 0, 'id': 1, 'name': 1, 'date': 1}))

    def get_value_from_session(self, sessionid, key):
        """Key-value lookup for the provided session id and key

        :type sessionid: str
        :type key: str
        """
        filter_dict = {'_id': 0, key: 1}
        return self._sessions.find_one({'id': sessionid}, filter_dict)[key]

    def get_time_range(self, sessionid, carnumber, datatype, channel, starttime, endtime):
        """ Get a filtered range of data from a session

        :param sessionid: the sessions unique id
        :param carnumber: the driver/car number
        :param datatype: one of the available datatypes, e.g. 'data' or 'position'
        :param channel: one of the available F1 Telemetry channel
        :param starttime: range start
        :param endtime: range end

        :type sessionid: str
        :type carnumber: str
        :type datatype: str
        :type channel: str
        :type starttime: datetime or pandas.Timestamp
        :type endtime: datetime or pandas.Timestamp

        :return: PyMongo Cursor for the selected time range and for the selected car.
        Results are filtered so they only contain the time and the selected channel
        """
        session = self._dbclient[sessionid]
        collection = session[carnumber + '-' + datatype]
        channel_filter = {'_id': 0, 'time': 1, channel: 1}
        return collection.find({'time': {'$gte': starttime, '$lt': endtime}}, channel_filter)

    def get_timing_data(self, sessionid, drivernumber, lap=(), timerange=(), starts_in=True, ends_in=True):
        assert not (lap and timerange), "Lap and Timerange are mutually exclusive"

        collection = self._dbclient[sessionid]['timingdata']

        if lap:
            if lap == 'fastest':
                timing_data = list(collection.find({'DriverNumber': drivernumber}).sort('LapTime', 1).limit(1))
            elif isinstance(lap, (tuple, list)) and all(isinstance(itm, (int, float)) for itm in lap):
                timing_data = list(collection.find({'DriverNumber': drivernumber, 'LapNumber': {'$in': lap}}))
            elif isinstance(lap, (int, float)):
                timing_data = list(collection.find({'DriverNumber': drivernumber, 'LapNumber': lap}))
            else:
                raise ValueError("Invalid value for lap: {}".format(lap))

        elif timerange:
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
        channels = {'_id': 0, 'SessionTime': 1}
        if filter_channels:
            for name in filter_channels:
                channels[name] = 1

        telemetry = list(self._dbclient[session_id]['telemetry'].find({'LapId': lap_id}, channels))
        return telemetry

    def insert_many(self, db_name, collection_name, data):
        """Insert multiple documents into a collection

        :type db_name: str
        :type collection_name: str
        :type data: list or tuple or pandas.DataFrame
        """
        self._dbclient[db_name][collection_name].insert_many(data)
