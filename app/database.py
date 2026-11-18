import os
from pymongo import MongoClient, GEOSPHERE
from pymongo.database import Database

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "correos_valparaiso")

_client: MongoClient | None = None

def get_db() -> Database:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    db = _client[DB_NAME]

    db.cuarteles.create_index([("ubicacion", GEOSPHERE)])
    return db

_client = MongoClient(MONGO_URI, tz_aware=True, serverSelectionTimeoutMS=5000)