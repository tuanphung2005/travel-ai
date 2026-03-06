from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from datetime import datetime

from app.database import get_database


class JourneyRepository:
    """Repository for journey-related database operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.journeys
    
    async def get_by_id(self, journey_id: str) -> Optional[dict]:
        """Get a journey by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(journey_id)})
        except Exception:
            return None
    
    async def get_by_owner(self, owner_id: str) -> list[dict]:
        """Get all journeys owned by a user."""
        cursor = self.collection.find({"owner_id": owner_id})
        return await cursor.to_list(length=None)

    async def list_recent(self, limit: int = 20) -> list[dict]:
        """List recent journeys."""
        cursor = self.collection.find({}).sort("_id", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def create_journey(self, journey_doc: dict) -> Optional[str]:
        """Create a new journey document. (DISABLED: READ-ONLY)"""
        return str(ObjectId())
    
    async def delete_journey(self, journey_id: str) -> bool:
        """Delete a journey document by ID. (DISABLED: READ-ONLY)"""
        return True
    
    async def update_days(
        self, 
        journey_id: str, 
        days: list[dict]
    ) -> bool:
        """Update the days array of a journey with AI-generated itinerary. (DISABLED: READ-ONLY)"""
        return True
    
    async def add_stop_to_day(
        self,
        journey_id: str,
        day_number: int,
        stop: dict
    ) -> bool:
        """Add a single stop to a specific day. (DISABLED: READ-ONLY)"""
        return True
    
    async def remove_stop_from_day(
        self,
        journey_id: str,
        day_number: int,
        place_id: str
    ) -> bool:
        """Remove a stop from a specific day. (DISABLED: READ-ONLY)"""
        return True
    
    async def reorder_stops(
        self,
        journey_id: str,
        day_number: int,
        stops: list[dict]
    ) -> bool:
        """Replace all stops in a day (for reordering). (DISABLED: READ-ONLY)"""
        return True

def get_journey_repository() -> JourneyRepository:
    """Get JourneyRepository instance."""
    return JourneyRepository(get_database())
