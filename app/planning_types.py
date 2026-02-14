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


@dataclass
class PlannedStop:
    """A planned stop with all metadata."""
    place: PlaceData
    duration_minutes: int
    reason: str
    order: int
    travel_time_from_previous: int
    distance_from_previous_km: float
