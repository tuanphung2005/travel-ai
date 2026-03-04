"""
Repository layer for database operations.
Handles all MongoDB queries and data transformation.
"""
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from datetime import datetime

from app.database import get_database
from app.ai_planner import PlaceData


class PlaceRepository:
    """Repository for place-related database operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.places
    
    async def get_by_id(self, place_id: str) -> Optional[dict]:
        """
        Get a single place by ID.
        
        Args:
            place_id: The place's ObjectId as string
        
        Returns:
            Place document or None
        """
        try:
            return await self.collection.find_one({"_id": ObjectId(place_id)})
        except Exception:
            return None
    
    async def get_by_ids(self, place_ids: list[str]) -> list[dict]:
        """
        Get multiple places by their IDs.
        
        Args:
            place_ids: List of place ObjectIds as strings
        
        Returns:
            List of place documents
        
        MongoDB Query:
            db.places.find({ _id: { $in: [ObjectId(...), ...] } })
        """
        object_ids = []
        for pid in place_ids:
            try:
                object_ids.append(ObjectId(pid))
            except Exception:
                continue
        
        if not object_ids:
            return []
        
        cursor = self.collection.find({"_id": {"$in": object_ids}})
        return await cursor.to_list(length=None)
    
    async def get_all_approved(self, limit: int = 100) -> list[dict]:
        """
        Get all approved places.
        
        Args:
            limit: Maximum number of places to return
        
        Returns:
            List of approved place documents
        
        MongoDB Query:
            db.places.find({ status: "APPROVED" }).limit(100)
        """
        cursor = self.collection.find(
            {"status": "APPROVED"}
        ).limit(limit)
        return await cursor.to_list(length=None)
    
    async def get_by_category(
        self, 
        category: str, 
        limit: int = 50
    ) -> list[dict]:
        """
        Get places by category.
        
        Args:
            category: ATTRACTION, HOTEL, or RESTAURANT
            limit: Maximum number to return
        
        Returns:
            List of place documents
        
        MongoDB Query:
            db.places.find({ 
                category: "ATTRACTION", 
                status: "APPROVED" 
            }).sort({ rating: -1 }).limit(50)
        """
        cursor = self.collection.find(
            {"category": category, "status": "APPROVED"}
        ).sort("rating", -1).limit(limit)
        return await cursor.to_list(length=None)
    
    async def search_nearby(
        self,
        longitude: float,
        latitude: float,
        max_distance_meters: int = 5000
    ) -> list[dict]:
        """
        Find places near a geographic point.
        Requires a 2dsphere index on the location field.
        
        Args:
            longitude: Center point longitude
            latitude: Center point latitude  
            max_distance_meters: Maximum distance in meters
        
        Returns:
            List of nearby places
        
        MongoDB Query:
            db.places.find({
                location: {
                    $near: {
                        $geometry: { type: "Point", coordinates: [lon, lat] },
                        $maxDistance: 5000
                    }
                }
            })
        """
        cursor = self.collection.find({
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [longitude, latitude]
                    },
                    "$maxDistance": max_distance_meters
                }
            },
            "status": "APPROVED"
        })
        return await cursor.to_list(length=None)
    
    @staticmethod
    def to_place_data(doc: dict) -> PlaceData:
        """
        Convert MongoDB document to PlaceData for AI planning.
        
        Args:
            doc: MongoDB document
        
        Returns:
            PlaceData instance
        """
        coords = doc.get("location", {}).get("coordinates", [0, 0])
        price_level = int(doc.get("priceLevel", 0) or 0)
        fallback_cost = {
            0: 80000,
            1: 120000,
            2: 220000,
            3: 380000,
            4: 600000,
        }.get(price_level, 150000)

        tags = [str(tag).strip().lower() for tag in doc.get("tags", []) if str(tag).strip()]
        inferred_healing = 4 if any(tag in {"healing", "nature", "quiet", "park", "spa"} for tag in tags) else 3
        inferred_crowd = 2 if any(tag in {"quiet", "hidden", "less-crowded"} for tag in tags) else 3

        return PlaceData(
            id=str(doc["_id"]),
            name=doc.get("name", "Unknown"),
            longitude=coords[0] if len(coords) > 0 else 0,
            latitude=coords[1] if len(coords) > 1 else 0,
            category=doc.get("category", "ATTRACTION"),
            rating=doc.get("rating", 0.0),
            review_count=doc.get("reviewCount", 0),
            tags=doc.get("tags", []),
            estimated_cost_vnd=int(doc.get("estimated_cost_vnd", fallback_cost) or fallback_cost),
            avg_visit_duration_min=int(doc.get("avg_visit_duration_min", 75) or 75),
            healing_score=int(doc.get("healing_score", inferred_healing) or inferred_healing),
            crowd_level=int(doc.get("crowd_level", inferred_crowd) or inferred_crowd),
            image_url=doc.get("image_url"),
        )


class JourneyRepository:
    """Repository for journey-related database operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.journeys
    
    async def get_by_id(self, journey_id: str) -> Optional[dict]:
        """
        Get a journey by ID.
        
        Args:
            journey_id: The journey's ObjectId as string
        
        Returns:
            Journey document or None
        
        MongoDB Query:
            db.journeys.findOne({ _id: ObjectId("...") })
        """
        try:
            return await self.collection.find_one({"_id": ObjectId(journey_id)})
        except Exception:
            return None
    
    async def get_by_owner(self, owner_id: str) -> list[dict]:
        """
        Get all journeys owned by a user.
        
        Args:
            owner_id: The owner's user ID
        
        Returns:
            List of journey documents
        
        MongoDB Query:
            db.journeys.find({ owner_id: "..." })
        """
        cursor = self.collection.find({"owner_id": owner_id})
        return await cursor.to_list(length=None)

    async def list_recent(self, limit: int = 20) -> list[dict]:
        """
        List recent journeys.

        Args:
            limit: Maximum number of journeys to return

        Returns:
            List of journey documents sorted by newest first
        """
        cursor = self.collection.find({}).sort("_id", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def create_journey(self, journey_doc: dict) -> Optional[str]:
        """
        Create a new journey document.

        Args:
            journey_doc: Journey document payload

        Returns:
            Inserted journey ID as string or None on failure
        """
        try:
            result = await self.collection.insert_one(journey_doc)
            return str(result.inserted_id)
        except Exception:
            return None
    
    async def delete_journey(self, journey_id: str) -> bool:
        """
        Delete a journey document by ID.

        Args:
            journey_id: The journey's ObjectId as string

        Returns:
            True if deleted successfully
        """
        try:
            result = await self.collection.delete_one({"_id": ObjectId(journey_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    async def update_days(
        self, 
        journey_id: str, 
        days: list[dict]
    ) -> bool:
        """
        Update the days array of a journey with AI-generated itinerary.
        
        Args:
            journey_id: The journey's ObjectId as string
            days: New days array with stops
        
        Returns:
            True if update successful
        
        MongoDB Query:
            db.journeys.updateOne(
                { _id: ObjectId("...") },
                { 
                    $set: { 
                        days: [...],
                        updated_at: new Date()
                    } 
                }
            )
        """
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(journey_id)},
                {
                    "$set": {
                        "days": days,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def add_stop_to_day(
        self,
        journey_id: str,
        day_number: int,
        stop: dict
    ) -> bool:
        """
        Add a single stop to a specific day.
        
        Args:
            journey_id: The journey's ObjectId as string
            day_number: Which day to add the stop to
            stop: Stop data to add
        
        Returns:
            True if successful
        
        MongoDB Query:
            db.journeys.updateOne(
                { _id: ObjectId("..."), "days.day_number": 1 },
                { $push: { "days.$.stops": {...} } }
            )
        """
        try:
            result = await self.collection.update_one(
                {
                    "_id": ObjectId(journey_id),
                    "days.day_number": day_number
                },
                {
                    "$push": {"days.$.stops": stop},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def remove_stop_from_day(
        self,
        journey_id: str,
        day_number: int,
        place_id: str
    ) -> bool:
        """
        Remove a stop from a specific day.
        
        Args:
            journey_id: The journey's ObjectId as string
            day_number: Which day to remove from
            place_id: The place ID to remove
        
        Returns:
            True if successful
        
        MongoDB Query:
            db.journeys.updateOne(
                { _id: ObjectId("..."), "days.day_number": 1 },
                { $pull: { "days.$.stops": { place_id: "..." } } }
            )
        """
        try:
            result = await self.collection.update_one(
                {
                    "_id": ObjectId(journey_id),
                    "days.day_number": day_number
                },
                {
                    "$pull": {"days.$.stops": {"place_id": place_id}},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def reorder_stops(
        self,
        journey_id: str,
        day_number: int,
        stops: list[dict]
    ) -> bool:
        """
        Replace all stops in a day (for reordering).
        
        Args:
            journey_id: The journey's ObjectId as string
            day_number: Which day to update
            stops: New ordered list of stops
        
        Returns:
            True if successful
        
        MongoDB Query:
            db.journeys.updateOne(
                { _id: ObjectId("..."), "days.day_number": 1 },
                { $set: { "days.$.stops": [...] } }
            )
        """
        try:
            result = await self.collection.update_one(
                {
                    "_id": ObjectId(journey_id),
                    "days.day_number": day_number
                },
                {
                    "$set": {
                        "days.$.stops": stops,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False


def get_place_repository() -> PlaceRepository:
    """Get PlaceRepository instance."""
    return PlaceRepository(get_database())


def get_journey_repository() -> JourneyRepository:
    """Get JourneyRepository instance."""
    return JourneyRepository(get_database())
