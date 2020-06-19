import sys
import os

import pymongo
import pandas as pd
import numpy as np

import fastf1
fastf1.utils.enable_cache('D:\\Dateien\\FF1Data')

# Delete current elements which are not updated? Be careful with this setting!
DELETE_NOT_UPDATED = True

# Event selection
# YEAR = 2020
# GP = 'testing'
# EVENT = 3
YEAR = 2019
GP = 10
EVENT = 'R'

# Database names
# SESSION_ID = '2020-101-3'
SESSION_ID = '2019-10-5'

# #################
info_labels = ['Time',
               'DriverNumber',
               'LapTime',
               'LapNumber',
               'Stint',
               'PitOutTime',
               'PitInTime',
               'Sector1Time',
               'Sector2Time',
               'Sector3Time',
               'SpeedI1',
               'SpeedI2',
               'SpeedFL',
               'SpeedST',
               'Compound',
               'TyreLife',
               'FreshTyre',
               'Team',
               'Driver',
               'LapStartDate']

timedelta_conv = ['Time', 'LapTime', 'PitInTime', 'PitOutTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']


mongo_client = pymongo.MongoClient('mongodb://localhost:27017')
database = mongo_client[SESSION_ID]

session = fastf1.core.get_session(YEAR, GP, EVENT)
session.load_laps()


def load_info_data():
    """Load info data like Lap Times, Sector Times, Top Speeds, LapStartTime, Tires, ... from FastF1

    Data can be added to the database, existing entries will be updated.
    Optionally, not updated entries will be deleted.

    Existing laps will not technically be updated. Instead they will be deleted and inserted newly.
    This only needs two db calls and less filtering (i.e. easier for me)

    Updating is dumb, meaning it does not check for actually changed data.
    If an id exists in current and new data, it will be updated.

    If LapStartDate, LapEndDate or LapTime are not available, those values are set to 'inf' (string).
    Reason: - None, 0, NaN and similar are not possible because they are returned by mongodb $min queries
            - Infinity (e.g. numpy.inf) is supported by mongodb but not by JSON; therefore it would need to be converted by the server
              I don't want to add a check for that in the server between db query and sending response for performance reasons
    """
    collection = database['timingdata']

    # get all existing ids in collection
    current_ids = [res['_id'] for res in collection.find({}, {'_id': 1})]

    # ####### Prepare Data ########
    # filter out telemetry
    data = session.laps.filter(info_labels)

    # create a new column 'LapEndDate'. This is done to allow more efficient database querying
    def lap_end_date_sum(d):
        r = d['LapStartDate'] + d['LapTime']
        return pd.to_datetime(r) if not pd.isnull(r) else 'inf'  # convert to datetime right away; this needs to be done anyway

    lap_end_date = pd.DataFrame({'LapEndDate': data.filter(['LapTime', 'LapStartDate']).aggregate(lap_end_date_sum, axis="columns")})
    data = data.join(lap_end_date)

    # convert LapStartTime to python builtin datetime
    data['LapStartDate'] = data['LapStartDate'].apply(lambda itm: 'inf' if pd.isnull(itm) else pd.to_datetime(itm))

    # mongodb does not support pd.Timedelta; convert to seconds (floating point)
    for key in timedelta_conv:
        data[key] = data[key].apply(lambda itm: itm.total_seconds())

    # if LapTime is NaN replace with 'inf'; mongodb will return NaN as minimum value but I need to be able to search with min
    data['LapTime'] = data['LapTime'].apply(lambda itm: 'inf' if pd.isnull(itm) else itm)

    data = data.reset_index().rename(columns={'index': '_id'}).to_dict(orient='records')

    # modify DB
    collection.drop()
    collection.insert_many(data)

    # DB preparation
    collection.create_index('LapTime')


def load_telemetry():

    collection = database['telemetry']

    # get all existing ids in collection
    # current_ids = [res['_id'] for res in collection.find({}, {'_id': 1})]

    for num, data in session.laps.telemetry.iteritems():
        # telemetry data for one lap
        print(num)
        if isinstance(data, pd.DataFrame):
            # check for ids which already exist in the db
            # update_ids = [_id for _id in data.index if _id in current_ids]

            data['Time'] = data['Time'].apply(lambda itm: itm.total_seconds())
            data['SessionTime'] = data['SessionTime'].apply(lambda itm: itm.total_seconds())

            data['LapId'] = num

            # create list of dicts for passing to .insert_many(); include Series indices
            # data = data.reset_index().rename(columns={'index': '_id'}).to_dict(orient='records')
            data = data.reset_index().to_dict(orient='records')

            # modify DB
            # if update_ids:
            #     collection.delete_many({'_id': {'$in': update_ids}})  # delete data points which should be 'updated'
            if data:
                collection.insert_many(data)  # insert new and 'updated'


def get_confirmation():
    """get user confirmation; return True/False"""
    answer = None
    while answer not in ['Y', 'y', 'N', 'n']:
        answer = input("Continue? (Y/N)  ")
    if answer in 'Yy':
        return True
    else:
        return False


if __name__ == '__main__':
    # load_info_data()
    load_telemetry()
