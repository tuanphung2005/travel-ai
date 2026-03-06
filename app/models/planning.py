from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional
from datetime import datetime

Mood = Literal["RESET_HEALING", "CHILL_CAFE", "NATURE_EXPLORE", "FOOD_LOCAL"]

class AIPlanRequest(BaseModel):
    """Request body for AI itinerary planning."""
    total_days: Optional[int] = Field(default=None, ge=1)
    total_budget_vnd: int = Field(ge=0, description="Total trip budget in VND")
    daily_budget_vnd: int = Field(ge=0, description="Daily budget cap in VND")
    mode: Literal["solo", "group"] = Field(default="solo")
    requester_user_id: Optional[str] = Field(default=None, description="Caller user ID for authorization checks")
    mood: Optional[Mood] = Field(default=None, description="Required when mode is solo")
    mood_distribution: Optional[dict[Mood, float]] = Field(
        default=None,
        description="Required when mode is group; weights should sum to ~1.0"
    )
    start_location: Optional[dict[str, float]] = Field(
        default=None,
        description="Optional starting point with keys: latitude, longitude"
    )
    max_places_per_day: int = Field(default=5, ge=1, le=5)
    must_include_categories: Optional[list[str]] = None
    exclude_categories: Optional[list[str]] = None

    hours_per_day: float = Field(default=8, ge=1, le=16, description="Deprecated compatibility field")
    travel_style: Literal["sightseeing", "relaxing", "balanced"] = Field(
        default="balanced",
        description="Deprecated compatibility field"
    )
    place_ids: Optional[list[str]] = Field(
        default=None,
        description="Specific place IDs to plan. If empty, AI will suggest from all places."
    )

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
    mood_score_breakdown: dict[Mood, float] = Field(default_factory=dict)
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
    explanations: list[str] = []
    summary: str

class AICandidatePlace(BaseModel):
    """A place evaluated by the AI for inclusion."""
    place_id: str
    place_name: str
    category: str
    rating: float
    estimated_cost_vnd: int
    final_score: float
    mood_score_breakdown: dict[Mood, float] = Field(default_factory=dict)
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
    candidate_pool: list[AICandidatePlace] = []
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
    total_budget_vnd: int = 0
    daily_budget_vnd: int = 0
    mode: Literal["solo", "group"] = "solo"
    mood: Optional[Mood] = "NATURE_EXPLORE"
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
