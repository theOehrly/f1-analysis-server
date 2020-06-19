from f1API.livetiming.datasources import WSFileSource
from f1API.livetiming.core import LiveTimingSession
from src.backendtools import DatabaseConnector
from f1API.livetiming.analysis import remap_pos_to_data

import time

CREATE_MERGED = True

SESSION_ID = '2020-102-5'

source = WSFileSource('recordings/sample2.jsonlist')
# source.INTERESTING_CARS = ('33', '23', '99')
# source.MAX_NUMBER_OF_MESSAGES = 20

session = LiveTimingSession()

source.read_data_to_session(session)

db = DatabaseConnector('mongodb://localhost:27017')

start_time = time.time()

cnt = 0
for number in session.list_car_numbers():
    cnt += 1
    print("processing car number {}".format(number))
    car = session.get_car(number)

    print("\t...data")
    data = car.data.reset_index().rename(columns={'index': 'time'}).to_dict(orient='records')
    db.insert_many(SESSION_ID, '{}-data'.format(number), data)

    print("\t...position")
    position = car.position.reset_index().rename(columns={'index': 'time'}).to_dict(orient='records')
    db.insert_many(SESSION_ID, '{}-position'.format(number), position)

    print("\t...merge")
    if CREATE_MERGED:
        merged = remap_pos_to_data(car).reset_index().rename(columns={'index': 'time'}).to_dict(orient='records')
        db.insert_many(SESSION_ID, '{}-merge-rp'.format(number), merged)


end_time = time.time()
duration = round(end_time - start_time)

processed_time_range = (car.data.index[-1] - car.data.index[0]).seconds

print("###############################\n\n")
print("Processed {} seconds of data with {} cars".format(processed_time_range, cnt))
print("Took {} seconds to process".format(duration))

