"""Shared types for itinerary planning."""
from dataclasses import dataclass


@dataclass
class PlaceData:
    """Internal representation of a place for planning."""
    id: str
    name: str
    latitude: float
    longitude: float
    category: str
    rating: float
    review_count: int
    tags: list[str]
    estimated_cost_vnd: int
    avg_visit_duration_min: int
    healing_score: int
    crowd_level: int
    price_level: int = 0
    image_url: str | None = None


@dataclass
class PlannedStop:
    """A planned stop with all metadata."""
    place: PlaceData
    duration_minutes: int
    reason: str
    order: int
    travel_time_from_previous: int
    distance_from_previous_km: float
    estimated_cost_vnd: int
    final_score: float
    mood_score_breakdown: dict[str, float]
