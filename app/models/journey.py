from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Stop(BaseModel):
    """A stop in the journey itinerary."""
    place_id: str
    place_name: str
    estimated_duration_minutes: int
    reason: str
    order: int
    # Additional info for frontend display
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category: Optional[str] = None

class DayPlan(BaseModel):
    """A single day in the journey."""
    day_number: int
    date: datetime
    stops: list[Stop] = []
    total_duration_minutes: int = 0
    total_travel_time_minutes: int = 0

class Journey(BaseModel):
    """Journey model matching MongoDB schema."""
    id: str = Field(alias="_id")
    name: str
    owner_id: str
    members: list[str] = []
    start_date: datetime
    end_date: datetime
    days: list[DayPlan] = []
    total_budget: float = 0
    status: Optional[str] = None
    
    class Config:
        populate_by_name = True
