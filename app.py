from flask import Flask, jsonify, request
from flask_cors import CORS

from webserver import dataprovider, lookuptables

db = dataprovider.db

# configuration
DEBUG = True

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)

# enable CORS TODO: how does this work? Set correctly for prod
CORS(app, resources={r'/*': {'origins': '*'}})


@app.route('/info/events', methods=['GET'])
def get_events():
    events = db.get_events_names()
    response_obj = {'data': events, 'status': 'success', 'msg': ''}
    return jsonify(response_obj)


@app.route('/info/sessions/<eventid>', methods=['GET'])
def get_sessions_for_event(eventid):
    sessions = db.get_sessions_names(eventid=eventid)
    response_obj = {'data': sessions, 'status': 'success', 'msg': ''}
    return jsonify(response_obj)


@app.route('/info/drivers', methods=['GET'])
def get_drivers():
    data = lookuptables.get_driver_abbs()
    response_obj = {'data': data, 'status': 'success', 'msg': ''}
    return jsonify(response_obj)


@app.route('/info/channels', methods=['GET'])
def get_telemetry_channels():
    response_obj = {'data': lookuptables.json_channel_names, 'status': 'success', 'msg': ''}
    return jsonify(response_obj)


@app.route('/data/telemetry', methods=['POST'])
def get_telemetry_data():
    response_object = {'status': 'success', 'msg': ''}
    payload = request.get_json()

    data = dataprovider.get_telemetry_data(payload)

    response_object['data'] = data

    return jsonify(response_object)


if __name__ == '__main__':
    app.run()
