from src.backendtools import DatabaseConnector

db = DatabaseConnector('mongodb://localhost:27017')

evts = db.get_sessions_names()

print(evts)



