from dbconnector import DatabaseConnector
from lookuptables import driver_query
from pandas import Timestamp
from datetime import datetime

db = DatabaseConnector('mongodb://localhost:27017')


def get_plot_data(payload, response_object):
    # get the sessions date (as in year, month, day) and create the time stamps
    date = db.get_value_from_session(payload['session'], 'date').strftime('%Y-%m-%d')
    start_time = Timestamp(date + 'T' + payload['startTime'])
    end_time = Timestamp(date + 'T' + payload['endTime'])

    response_object['drivers'] = dict()

    # query the database individually for each driver (one collection per driver)
    for car_number in payload['drivers']:
        car_data = list()
        for data_row in db.get_time_range(payload['session'], car_number, 'data', payload['channel'], start_time, end_time):
            data_row['time'] = data_row['time'].isoformat()
            car_data.append(data_row)

        response_object['drivers'][car_number] = car_data

    return response_object


def datetime_from_timestring(year, month, day, timestring):
    hh, mm, ss = timestring.split(':')
    return datetime(year, month, day, int(hh), int(mm), int(ss))


def get_telemetry_data(payload):
    ret = list()

    ch_name = payload['channel']
    sid = payload['session']

    for driver in payload['drivers']:
        driver_number = driver_query(by='Abb', value=driver, get='Number')

        if payload['selectBy'] == 'fastest':
            timing_data = db.get_timing_data(sid, driver_number, lap='fastest')

        elif payload['selectBy'] == 'time':
            # currently everything works in UTC; event local time might be preferred for later
            start = datetime.utcfromtimestamp(payload['timeStartValue']/1000)
            end = datetime.utcfromtimestamp(payload['timeEndValue']/1000)
            timing_data = db.get_timing_data(sid,
                                             driver_number,
                                             timerange=(start, end),
                                             starts_in=bool(payload['timeStartIn']),
                                             ends_in=bool(payload['timeEndIn']))

        elif payload['selectBy'] == 'laps':
            timing_data = db.get_timing_data(sid, driver_number, lap=payload['laps'])

        else:
            raise ValueError("Invalid value for 'selectBy': {}".format(payload['selectBy']))

        for lap in timing_data:
            lap_id = lap['_id']  # list should always only have one item; there should be only one fastest lap
            telemetry = db.get_lap_telemetry(sid, lap_id, filter_channels=(ch_name,))
            ret.append({'driver': driver, 'telemetry': telemetry, 'laptime': lap['LapTime'], 'lapnumber': lap['LapNumber']})
            
    return ret
