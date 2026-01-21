"""
MongoDB database connection using Motor (async MongoDB driver).
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings

# Global database client and database instances
client: AsyncIOMotorClient | None = None
database: AsyncIOMotorDatabase | None = None


async def connect_to_mongo():
    """
    Establish connection to MongoDB Atlas.
    Called on application startup.
    """
    global client, database
    settings = get_settings()
    
    client = AsyncIOMotorClient(settings.MONGO_URI)
    database = client[settings.DB_NAME]
    
    # Test connection
    await client.admin.command('ping')
    print(f"✅ Connected to MongoDB Atlas - Database: {settings.DB_NAME}")


async def close_mongo_connection():
    """
    Close MongoDB connection.
    Called on application shutdown.
    """
    global client
    if client:
        client.close()
        print("🔌 MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance."""
    if database is None:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    return database
