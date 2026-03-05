from pydantic import BaseModel, Field
from typing import Optional

class Location(BaseModel):
    """Geographic location with coordinates."""
    type: str = "Point"
    coordinates: list[float]  # [longitude, latitude]

class Place(BaseModel):
    """Place model matching MongoDB schema."""
    id: str = Field(alias="_id")
    google_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    category: str
    address: Optional[str] = None
    location: Location
    rating: Optional[float] = 0.0
    reviewCount: Optional[int] = 0
    priceLevel: Optional[int] = 0
    tags: list[str] = []
    estimated_cost_vnd: Optional[int] = 0
    avg_visit_duration_min: Optional[int] = 75
    healing_score: Optional[int] = 3
    crowd_level: Optional[int] = 3
    image_url: Optional[str] = None
    
    class Config:
        populate_by_name = True
