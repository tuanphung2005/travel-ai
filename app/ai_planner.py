"""Backward-compatible facade for itinerary planning modules."""

from app.planning_types import PlaceData, PlannedStop
from app.planning_utils import (
    TRAVEL_STYLE_CONFIG,
    AVERAGE_TRAVEL_SPEED_KMH,
    haversine_distance,
    estimate_travel_time,
    build_distance_matrix,
    calculate_place_score,
    cluster_places_by_proximity,
    optimize_route_order,
    calculate_stop_duration,
    generate_stop_reason,
)
from app.itinerary_planner_core import ItineraryPlanner

__all__ = [
    "PlaceData",
    "PlannedStop",
    "TRAVEL_STYLE_CONFIG",
    "AVERAGE_TRAVEL_SPEED_KMH",
    "haversine_distance",
    "estimate_travel_time",
    "build_distance_matrix",
    "calculate_place_score",
    "cluster_places_by_proximity",
    "optimize_route_order",
    "calculate_stop_duration",
    "generate_stop_reason",
    "ItineraryPlanner",
]
