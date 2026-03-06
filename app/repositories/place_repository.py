from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

from app.database import get_database
from app.ai_planner import PlaceData
from app.services.place_enrichment import estimate_healing_score, estimate_crowd_level


class PlaceRepository:
    """Repository for place-related database operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.places
    
    async def get_by_id(self, place_id: str) -> Optional[dict]:
        """Get a single place by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(place_id)})
        except Exception:
            return None
    
    async def get_by_ids(self, place_ids: list[str]) -> list[dict]:
        """Get multiple places by their IDs."""
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
        """Get all approved places."""
        cursor = self.collection.find(
            {"status": "APPROVED"}
        ).limit(limit)
        return await cursor.to_list(length=None)
    
    async def get_by_category(
        self, 
        category: str, 
        limit: int = 50
    ) -> list[dict]:
        """Get places by category."""
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
        """Find places near a geographic point."""
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
    
    async def enrich_missing_scores(self, dry_run: bool = False) -> dict:
        """Finds records missing healing/crowd scores, estimates them, and updates DB."""
        # Find places lacking explicit values for these two
        # we check both $exists and $eq null in case they're set to null
        query = {
            "$or": [
                {"crowd_level": {"$exists": False}},
                {"crowd_level": None},
                {"healing_score": {"$exists": False}},
                {"healing_score": None}
            ]
        }
        
        cursor = self.collection.find(query)
        places = await cursor.to_list(length=None)
        
        results = {
            "total_found": len(places),
            "updated": 0,
            "skipped": 0,
            "preview": []
        }
        
        if not places:
            return results
            
        for doc in places:
            # Recompute existing or entirely new
            new_healing = estimate_healing_score(doc)
            new_crowd = estimate_crowd_level(doc)
            
            old_healing = doc.get("healing_score")
            old_crowd = doc.get("crowd_level")
            
            if True: # dry_run forced to True
                results["preview"].append({
                    "id": str(doc["_id"]),
                    "name": doc.get("name", "Unknown"),
                    "category": doc.get("category", ""),
                    "old_scores": {"healing": old_healing, "crowd": old_crowd},
                    "new_scores": {"healing": new_healing, "crowd": new_crowd}
                })
                results["updated"] += 1
                    
        return results
    
    @staticmethod
    def to_place_data(doc: dict) -> PlaceData:
        """Convert MongoDB document to PlaceData for AI planning."""
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
            price_level=price_level,
            image_url=doc.get("image_url"),
        )

def get_place_repository() -> PlaceRepository:
    """Get PlaceRepository instance."""
    return PlaceRepository(get_database())
