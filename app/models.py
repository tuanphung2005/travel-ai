"""
Pydantic models for request/response validation.
These models define the data structure for the API.
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


# ============================================
# Place Models
# ============================================

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
    category: Literal["ATTRACTION", "HOTEL", "RESTAURANT"]
    address: Optional[str] = None
    location: Location
    rating: Optional[float] = 0.0
    reviewCount: Optional[int] = 0
    priceLevel: Optional[int] = 0
    tags: list[str] = []
    
    class Config:
        populate_by_name = True


# ============================================
# Journey Models
# ============================================

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


# ============================================
# AI Planning Request/Response Models
# ============================================

class AIPlanRequest(BaseModel):
    """
    Request body for AI itinerary planning.
    
    Attributes:
        hours_per_day: Available hours for travel per day (1-16)
        travel_style: User's preferred travel style
            - sightseeing: More stops, shorter duration at each
            - relaxing: Fewer stops, longer duration at each
            - balanced: Moderate number of stops
        place_ids: Optional list of specific place IDs to include.
                   If not provided, uses all places in the journey.
    """
    hours_per_day: float = Field(default=8, ge=1, le=16, description="Available hours per day")
    travel_style: Literal["sightseeing", "relaxing", "balanced"] = Field(
        default="balanced",
        description="Travel style preference"
    )
    place_ids: Optional[list[str]] = Field(
        default=None,
        description="Specific place IDs to plan. If empty, AI will suggest from all places."
    )


class AIStopSuggestion(BaseModel):
    """AI-suggested stop with reasoning."""
    place_id: str
    place_name: str
    estimated_duration_minutes: int
    reason: str
    order: int
    travel_time_from_previous_minutes: int = 0
    distance_from_previous_km: float = 0.0
    latitude: float
    longitude: float
    category: str
    rating: float


class AIDayPlan(BaseModel):
    """AI-generated day plan with metadata."""
    day_number: int
    date: datetime
    stops: list[AIStopSuggestion]
    total_duration_minutes: int
    total_travel_time_minutes: int
    summary: str


class AIPlanResponse(BaseModel):
    """Response from AI planning endpoint."""
    journey_id: str
    journey_name: str
    total_days: int
    travel_style: str
    hours_per_day: float
    days: list[AIDayPlan]
    planning_notes: list[str]
    algorithm_version: str = "1.0.0"


class AIExplanation(BaseModel):
    """Detailed explanation of AI planning decisions."""
    journey_id: str
    algorithm_description: str
    distance_calculation: str
    grouping_strategy: str
    style_adjustments: dict
    constraints_applied: list[str]
    place_selection_criteria: list[str]


class CreateJourneyFromRelatedRequest(BaseModel):
    """Request body for creating a new journey from related places."""
    name: str = Field(min_length=1, max_length=200)
    owner_id: str = Field(min_length=1, max_length=200)
    start_date: datetime
    end_date: datetime
    seed_place_id: Optional[str] = Field(
        default=None,
        description="Optional seed place ID to find nearby and related places"
    )
    max_places: int = Field(
        default=12,
        ge=3,
        le=30,
        description="Maximum number of places to include in journey planning"
    )
    hours_per_day: float = Field(default=8, ge=1, le=16)
    travel_style: Literal["sightseeing", "relaxing", "balanced"] = "balanced"
    auto_plan: bool = Field(
        default=True,
        description="If true, runs AI planner and fills journey days immediately"
    )
    members: list[str] = []


class CreateJourneyFromRelatedResponse(BaseModel):
    """Response for journey creation from related places."""
    journey_id: str
    journey_name: str
    selected_places_count: int
    selected_place_ids: list[str]
    auto_planned: bool
    total_days: int
    planning_notes: list[str] = []
