from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
if not MONGODB_URL:
    raise RuntimeError("❌ MONGODB_URL not found in environment variables.")

client = AsyncIOMotorClient(MONGODB_URL)
DB_NAME = os.getenv("DB_NAME", "tn_internfair")
db = client[DB_NAME]

def get_db():
    """Returns the database instance; fails if not initialized."""
    if db is None:
        raise Exception("Database not initialized")
    return db

def to_oid(id_str: str):
    """Convert string to ObjectId if valid, else return as is."""
    try:
        if ObjectId.is_valid(id_str):
            return ObjectId(id_str)
    except:
        pass
    return id_str
