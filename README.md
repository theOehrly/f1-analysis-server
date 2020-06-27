F1 Analysis Server Backend
==========================

This is a primitive flask based backend server for my ``F1 Analysis Web App``.

(This is very much alpha grade software currently)  
The documentation is currently "ahead" of the implementation. It describes the development target but does 
not mirror the current state. 

MongoDB is used as a database. This server really only wraps database requests. The web app needs to be 
served separately.

The main objectives for this server are:
- use few resources, handle requests with as little work as possible
- provide a REST API
- as little code as possible
- only provide the most basic functionality necessary


The database is populated using some scripts. The ``Fast-F1`` python module is required for retrieving 
and pre-processing data.
See <https://github.com/theOehrly/Fast-F1>

A script for populating the database is available in ``/scripts``