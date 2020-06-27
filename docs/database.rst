======================
Database Documentation
======================

This project uses mongodb as a database. You need to provide the database separately.

******************
MongoDB structure
******************

Database "Info"
===============

Collection "Events"
-------------------

This collection holds information on available events.

And event is a race weekend or a test.

.. code:: json-object

    "id": "2019-1",
    "year": 2019,
    "name": "Australian GP",
    "type": "R",
    "note": "This race was upside down!"


- ``id``: A unique id for each event. It will usually be "``year`` - ``number``",
  except if not possible for some reason
- ``year``: Which year the event took place in
- ``name``: A name for the event.
- ``type``: What kind of event this is. "R" for race, "T" for test
- ``note``: Important notes about the event. Usually there shouldn't be any! This is
  only for special cases where something about the event or the data is out of the
  ordinary. The content of the note should be treated like a warning message.


Collection "Sessions"
---------------------

This collection holds information on available sessions.

.. code:: json-object

    "id": "2019-1-4",
    "eventid": "2019-1",
    "date": "2019-03-17T04:00:00.000",
    "name": "Qualifying",
    "trackmap": {
                    "X": [],
                    "Y": [],
                },
    "note": "Qualifying took place on sunday morning due to a giant
             lizard on track the day before!"

- ``id``: A unique id for each event, should usually be "``year`` - ``number`` - session_number",
  except if not possible for some reason.
- ``eventid``: The id of the parent event.
- ``date``: The specific time and date at which the event started (UTC).
- ``name``: A name for the session.
- ``trackmap``: An object containing two arrays of ``X`` and ``Y`` coordinates respectively.
  The unit of the coordinate system is unknown.
- ``note``: Important notes about the session. Usually there shouldn't be any! This is
  only for special cases where something about the session or the data is out of the
  ordinary. The content of the note should be treated like a warning message.


Database "<eventid>"
====================

There will be one database per event. The name of each database will be
each event's id. (See Database ``Info`` --> Collection ``Events``)

Each database will contain one collection of telemetry data per session.
The name of each collection will be the corresponding session's id.

Collection "<sessionid>"
------------------------

.. code:: json-object

    "Date": "2019-03-17T04:27:14.386",
    "RPM": 11820,
    "Speed": 251,
    "Gear": 6,
    "Throttle": 100,
    "Brake": 0,
    "DRS": 1,
    "Status": "OnTrack",
    "X": -1737.75,
    "Y": 1118.9166666666667,
    "Z": 1964.5833333333335,
    "InterpolatedPos": true,
    "InterpolatedData": false

- ``Date``: The specific date and time at which the data sample was recorded.
- ``RPM``: Engine RPM
- ``Speed``: Car speed in km/h
- ``Gear``: Currently selected gear
- ``Throttle``: Throttle input in percent
- ``Brake``: Brake input in percent
- ``DRS``: DRS open/closed and more modes? I haven't fully understood this yet.
- ``Status``: "OnTrack" or "OffTrack", "OnTrack" does not guarantee correct data!
- ``X``/``Y``/``Z``: Car coordinates, the unit of these values is unknown
- ``InterpolatedPos``/``InterpolatedData``: The sample rates for data and position are
  different. Therefore, interpolation is necessary to get both information at the same
  point in time. This flag tells which value was interpolated. (Can be both)
