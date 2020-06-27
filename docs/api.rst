=================
API Documentation
=================

This page details the JSON format used to transmit data to the client.

The following is a list of all possible URL paths and the response you can expect.

Every response contains a `status` and a `message`. These are currently unused but may be used
in the future to communicate errors and error messages or similar. Either for internal errors or
errors in the users input.

NO special error handling is done for http status codes. For example, if you are not authorized to access the server,
you will get a HTTP status code 403 (Forbidden) an NO JSON. In my opinion this is the expected behaviour.

It may happen that functionality which is implemented at a later point in time may be incompatible with older
events. For example, this could happen if additional data is required in the DB. Updating all past events may not be
feasible. In this case, the server will return HTTP status code 501 - Not Implemented.

The functionality of the API is very limited. This is intentional, as the idea is to do is as little data processing as
possible on the server. The client should request data and then process it locally.
For how I intend to use this project, the budget for operating a server is basically zero. Therefore server resources
must be used wisely. More complicated data visualization needs to be computed on the client side.

**List of current telemetry channels**

=== =======
ID  Name
=== =======
0   RPM
2   Speed
3   Gear
4   Throttle
5   Brake
45  DRS
=== =======



Available Events (/info/events) [GET]
=====================================
List all events which are available from the server.

An event is a race weekend or a test.
The event consist of multiple sessions.
For pre-season or in-season testing, the test is considered an event, with each test day
being a session.

.. code:: json

  { "data":
    [
      {
        "id": "YYYY-NN",
        "number": 01,
        "name": "Name of the Event, e.g. 'Austrian Grand Prix'",
        "type": "'R' or 'T' (Race Weekend or Testing)",
        "sessions": ["FP1", "FP2", "FP3", "Q", "R"],
      },
    ],
  "status": "success",
  "msg": ""}

- `data` can contain multiple event objects
- `id` is the a combination of year (YYYY) and event number (NN)
- `sessions` lists all available sessions (can be empty)


Available Sessions (/info/sessions/<eventid>) [GET]
===================================================
List all sessions for a given event.

.. code:: json

  { "data":
    [
      {
        "id": "YYYY-NN-M",
        "eventid": "YYYY-NN",
        "date": "2019-03-20T14:00:00",
        "name": "Free Practice 1",
        "type": "FP1",
      },
    ],
  "status": "success",
  "msg": ""}

- `data` can contain multiple session objects
- `id` is the a combination of year (YYYY), event number (NN) and session type (M)
- `eventid` is the id of the parent event
- `type` can be any of ["FP1", "FP2", "FP3", "Q", "R"]


Available Drivers (/info/drivers) [GET]
=======================================
Returns an array of all drivers known to the server. This is not event specific.

This data is not expected to change very often. It is implemented to be requested from the server, so that a change in
driver line up does not require an update of the web client.

.. code:: json

  { "data":
    [
      {
        "number": 44,
        "abb": "HAM",
      },
    ],
  "status": "success",
  "msg": ""}

- `data` can contain multiple driver objects


Available Telemetry Channels (/info/channels) [GET]
===================================================

Return an array of all available telemetry channels.

This data is not expected to change very often. It is implemented to be requested from the server, so that a change of
channel names or numbers does not require an update of the web client.

.. code:: json

  { "data":
    [
      {
        "id": 2,
        "name": "Speed",
      },
    ],
  "status": "success",
  "msg": ""}

- `data` can contain multiple driver objects


Request Data (/data/telemetry) [POST]
===================================================

Request telemetry data from the server.


**POST Payload**

.. code::

  'session': str,
  'drivers': [str, str, ...]
  'channel': str
  'selectBy': str
  'laps': [int, int, ...]
  'timeStartValue': int or float
  'timeEndValue': int or float
  'timeStartIn': bool
  'timeEndIn': bool

- **session**: the session ID for which data is requested
- **drivers**: an array of driver numbers as strings
- **channel** is currently a string. This is expected to change very soon. It will then be an array of strings so that
  multiple channels can be requested simultaneously
- **selectBy** can be one of the following:
  - 'fastest': return the fastest lap (only)
  - 'laps': return the specified laps (by lap number) [requires payload **laps**]
  - 'time': return all laps which lie in between a start and end time
  [requires payload **timeStartValue**, **timeEndValue**, **timeStartIn**, **timeEndIn**]
  Invalid values will raise a ValueError.
- **laps**: an array of lap numbers as integers
- **timeStartValue**/**timeEndValue**: requested time range, values in milliseconds since the epoch, UTC, no timezones
- **timeStartIn**/**timeEndIn**: Whether the laps should start in the specified time range, end in the specified time range
  or both. Start and End can NOT both be False as this would be true for all laps. Currently this raises a ValueError.
  A check in the web client should prevent setting both values to False.



**Response**

.. code:: json

  { "data":
      [
        {
          "driver": 44,
          "telemetry": [
              {"SessionTime": 1354.446, "Speed": 356},
            ],
          "laptime": "1:20:25.645",
          "lapnumber": 15
        },
      ],
  "status": "success",
  "msg": ""}

- **data** can contain multiple objects, one for each driver and lap requested
- **telemetry** is an array of objects. Each object is guaranteed to have a **SessionTime** key. This is the elapsed
  time since the start of the session in seconds as a floating point number.
  Furthermore, one or more keys can be present, where each key is the name of a telemetry channel.
