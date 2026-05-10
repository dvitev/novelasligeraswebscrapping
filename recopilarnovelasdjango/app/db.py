import os
from pymongo import MongoClient
from pymongo.database import Database

_client = None


def get_db() -> Database:
    global _client
    if _client is None:
        _client = MongoClient(
            host=os.environ.get("MONGODB_HOST", "192.168.1.11"),
            port=int(os.environ.get("MONGODB_PORT", 27017)),
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
    return _client[os.environ.get("MONGODB_DATABASE", "recopilarnovelas")]


def get_client() -> MongoClient:
    global _client
    if _client is None:
        get_db()
    return _client


def close_connection():
    global _client
    if _client is not None:
        _client.close()
        _client = None