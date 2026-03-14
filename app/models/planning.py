from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional
from datetime import datetime

Mood = Literal["RESET_HEALING", "CHILL_CAFE", "NATURE_EXPLORE", "FOOD_LOCAL"]

class AIPlanRequest(BaseModel):
    """Request body for AI itinerary planning."""
    total_days: Optional[int] = Field(default=None, ge=1, description="Optional guardrail. Must match journey date range when provided.")
    total_budget_vnd: int = Field(ge=0, description="Total trip budget in VND", examples=[7000000])
    daily_budget_vnd: int = Field(ge=0, description="Daily budget cap in VND", examples=[1200000])
    mode: Literal["solo", "group"] = Field(default="solo", description="Planning mode: solo mood or group mixed mood.")
    requester_user_id: Optional[str] = Field(default=None, description="Caller user ID. Required in group mode for owner authorization.", examples=["user_123"])
    mood: Optional[Mood] = Field(default=None, description="Required when mode is solo", examples=["NATURE_EXPLORE"])
    mood_distribution: Optional[dict[Mood, float]] = Field(
        default=None,
        description="Required when mode is group; weights should sum to ~1.0"
    )
    start_location: Optional[dict[str, float]] = Field(
        default=None,
        description="Optional starting point with keys: latitude, longitude"
    )
    max_places_per_day: int = Field(default=5, ge=1, le=5, description="Hard cap on places selected per day.")
    must_include_categories: Optional[list[str]] = Field(default=None, description="Categories that must appear in itinerary when feasible.", examples=[["CAFE", "ATTRACTION"]])
    exclude_categories: Optional[list[str]] = Field(default=None, description="Categories to always exclude.", examples=[["NIGHTLIFE"]])

    hours_per_day: float = Field(default=8, ge=1, le=16, description="Deprecated compatibility field")
    travel_style: Literal["sightseeing", "relaxing", "balanced"] = Field(
        default="balanced",
        description="Deprecated compatibility field"
    )
    place_ids: Optional[list[str]] = Field(
        default=None,
        description="Specific place IDs to plan. If empty, AI will suggest from all places."
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_budget_vnd": 7000000,
                    "daily_budget_vnd": 1200000,
                    "mode": "solo",
                    "mood": "NATURE_EXPLORE",
                    "max_places_per_day": 4,
                    "must_include_categories": ["ATTRACTION", "CAFE"],
                    "exclude_categories": ["NIGHTLIFE"],
                    "travel_style": "balanced"
                },
                {
                    "total_budget_vnd": 9000000,
                    "daily_budget_vnd": 1500000,
                    "mode": "group",
                    "requester_user_id": "owner_001",
                    "mood_distribution": {
                        "RESET_HEALING": 0.3,
                        "CHILL_CAFE": 0.2,
                        "NATURE_EXPLORE": 0.3,
                        "FOOD_LOCAL": 0.2
                    },
                    "max_places_per_day": 5,
                    "travel_style": "sightseeing"
                }
            ]
        }
    }

    @model_validator(mode="after")
    def validate_mode_fields(self):
        if self.mode == "solo" and self.mood is None:
            raise ValueError("mood is required when mode='solo'")

        if self.mode == "group":
            if not self.mood_distribution:
                raise ValueError("mood_distribution is required when mode='group'")
            total_weight = sum(self.mood_distribution.values())
            if total_weight <= 0:
                raise ValueError("mood_distribution total weight must be > 0")

        return self

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
    estimated_cost_vnd: int = 0
    final_score: float = 0.0
    mood_score_breakdown: dict[str, float] = Field(default_factory=dict, description="Per-mood score components used in ranking.")
    is_hotel_anchor: bool = False

class AIDayPlan(BaseModel):
    """AI-generated day plan with metadata."""
    day_number: int
    date: datetime
    stops: list[AIStopSuggestion]
    total_duration_minutes: int
    total_travel_time_minutes: int
    total_estimated_cost_vnd: int
    total_distance_km: float
    spent_today: int
    remaining_today: int
    saved_vs_budget: int
    explanations: list[str] = Field(default_factory=list)
    summary: str
    weather: Optional[dict] = None

class AICandidatePlace(BaseModel):
    """A place evaluated by the AI for inclusion."""
    place_id: str
    place_name: str
    category: str
    rating: float
    estimated_cost_vnd: int
    final_score: float
    mood_score_breakdown: dict[str, float] = Field(default_factory=dict)
    reasoning: Optional[str] = None
    selected: bool = False

class AIPlanResponse(BaseModel):
    """Response from AI planning endpoint."""
    journey_id: str
    journey_name: str
    total_days: int
    mode: Literal["solo", "group"]
    mood_used: Optional[Mood] = None
    mood_distribution_used: Optional[dict[Mood, float]] = None
    total_budget_vnd: int
    daily_budget_vnd: int
    generated_at: datetime
    candidate_pool_size: int
    generation_time_ms: int
    hotel_name: Optional[str] = None
    accommodation_cost_vnd: int = 0
    num_nights: int = 0
    days: list[AIDayPlan]
    candidate_pool: list[AICandidatePlace] = Field(default_factory=list)
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
    travel_style: Literal["sightseeing", "relaxing", "balanced"] = Field(default="balanced")
    total_budget_vnd: int = Field(default=0, ge=0)
    daily_budget_vnd: int = Field(default=0, ge=0)
    mode: Literal["solo", "group"] = Field(default="solo")
    mood: Optional[Mood] = Field(default="NATURE_EXPLORE")
    auto_plan: bool = Field(
        default=True,
        description="If true, runs AI planner and fills journey days immediately"
    )
    members: list[str] = Field(default_factory=list)
    start_location: Optional[dict[str, float]] = Field(
        default=None,
        description="Optional start location with latitude and longitude"
    )
    must_include_categories: Optional[list[str]] = Field(
        default=None,
        description="Optional list of place categories that must be included"
    )
    exclude_categories: Optional[list[str]] = Field(
        default=None,
        description="Optional list of place categories to exclude"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Da Nang long weekend",
                "owner_id": "owner_001",
                "start_date": "2026-04-11T00:00:00Z",
                "end_date": "2026-04-13T00:00:00Z",
                "seed_place_id": "67fd123abc9876543210f111",
                "max_places": 12,
                "hours_per_day": 8,
                "travel_style": "balanced",
                "total_budget_vnd": 5000000,
                "daily_budget_vnd": 1200000,
                "mode": "solo",
                "mood": "NATURE_EXPLORE",
                "auto_plan": True,
                "members": ["owner_001"]
            }
        }
    }

class CreateJourneyFromRelatedResponse(BaseModel):
    """Response for journey creation from related places."""
    journey_id: str
    journey_name: str
    selected_places_count: int
    selected_place_ids: list[str]
    auto_planned: bool
    total_days: int
    planning_notes: list[str] = Field(default_factory=list)
    candidate_pool: Optional[list[AICandidatePlace]] = None
    days: Optional[list[AIDayPlan]] = None
    candidate_pool_size: Optional[int] = 0
    generation_time_ms: Optional[int] = 0
