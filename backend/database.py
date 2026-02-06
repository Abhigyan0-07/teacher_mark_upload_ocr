import os
from pymongo import MongoClient

# Default directly to your Atlas connection string and DB name.
# You can still override via environment variables if needed.
MONGO_URL = os.getenv(
    "MONGO_URL",
    "mongodb+srv://abhigyan1si23is001_db_user:ce0fPLuu1cZdqkv3@cluster0.a8thfro.mongodb.net/?appName=Cluster0",
)
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "marksdb")

_client: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URL)
    return _client


def get_db():
    client = get_mongo_client()
    return client[MONGO_DB_NAME]

