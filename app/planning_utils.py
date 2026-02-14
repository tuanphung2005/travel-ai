"""Pure planning utilities used by the itinerary planner."""
import math

from app.planning_types import PlaceData


TRAVEL_STYLE_CONFIG = {
    "sightseeing": {
        "description": "Fast-paced exploration with more stops",
        "base_duration_minutes": 45,
        "max_stops_per_day": 8,
        "min_stops_per_day": 4,
        "attraction_multiplier": 1.0,
        "restaurant_multiplier": 0.8,
        "buffer_time_minutes": 10,
    },
    "relaxing": {
        "description": "Leisurely pace with fewer stops",
        "base_duration_minutes": 120,
        "max_stops_per_day": 4,
        "min_stops_per_day": 2,
        "attraction_multiplier": 1.5,
        "restaurant_multiplier": 1.5,
        "buffer_time_minutes": 30,
    },
    "balanced": {
        "description": "Moderate pace with balanced exploration",
        "base_duration_minutes": 75,
        "max_stops_per_day": 6,
        "min_stops_per_day": 3,
        "attraction_multiplier": 1.2,
        "restaurant_multiplier": 1.0,
        "buffer_time_minutes": 20,
    },
}

AVERAGE_TRAVEL_SPEED_KMH = 25


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in km."""
    radius_earth_km = 6371.0

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return radius_earth_km * c


def estimate_travel_time(distance_km: float) -> int:
    """Estimate travel time in minutes from distance in km."""
    if distance_km <= 0:
        return 0

    time_hours = distance_km / AVERAGE_TRAVEL_SPEED_KMH
    time_minutes = int(time_hours * 60)
    return max(5, time_minutes)


def build_distance_matrix(places: list[PlaceData]) -> dict[str, dict[str, float]]:
    """Build a pairwise place distance matrix in km."""
    matrix = {}

    for p1 in places:
        matrix[p1.id] = {}
        for p2 in places:
            if p1.id == p2.id:
                matrix[p1.id][p2.id] = 0.0
            else:
                distance = haversine_distance(
                    p1.latitude,
                    p1.longitude,
                    p2.latitude,
                    p2.longitude,
                )
                matrix[p1.id][p2.id] = round(distance, 2)

    return matrix


def calculate_place_score(place: PlaceData, style: str) -> float:
    """Calculate priority score for place inclusion."""
    rating_score = (place.rating / 5.0) * 40
    review_score = min(20, math.log10(max(1, place.review_count)) * 5)

    category_bonuses = {
        "sightseeing": {"ATTRACTION": 40, "RESTAURANT": 20, "HOTEL": 10},
        "relaxing": {"ATTRACTION": 25, "RESTAURANT": 35, "HOTEL": 30},
        "balanced": {"ATTRACTION": 35, "RESTAURANT": 30, "HOTEL": 20},
    }

    category_score = category_bonuses.get(style, {}).get(place.category, 20)
    total_score = rating_score + review_score + category_score

    return round(total_score, 2)


def cluster_places_by_proximity(
    places: list[PlaceData],
    distance_matrix: dict[str, dict[str, float]],
    num_clusters: int,
) -> list[list[PlaceData]]:
    """Group places into geographically close clusters."""
    if not places:
        return []

    if len(places) <= num_clusters:
        return [[p] for p in places]

    sorted_places = sorted(places, key=lambda p: p.rating, reverse=True)
    used_ids: set[str] = set()

    seeds = [sorted_places[0]]
    used_ids.add(sorted_places[0].id)

    while len(seeds) < min(num_clusters, len(places)):
        best_place = None
        best_min_distance = -1

        for place in sorted_places:
            if place.id in used_ids:
                continue

            min_dist = min(distance_matrix[place.id][seed.id] for seed in seeds)
            if min_dist > best_min_distance:
                best_min_distance = min_dist
                best_place = place

        if best_place:
            seeds.append(best_place)
            used_ids.add(best_place.id)

    clusters = [[seed] for seed in seeds]

    for place in places:
        if place.id in used_ids:
            continue

        min_distance = float("inf")
        nearest_cluster_idx = 0

        for idx, cluster in enumerate(clusters):
            dist = distance_matrix[place.id][cluster[0].id]
            if dist < min_distance:
                min_distance = dist
                nearest_cluster_idx = idx

        clusters[nearest_cluster_idx].append(place)

    return clusters


def optimize_route_order(
    places: list[PlaceData],
    distance_matrix: dict[str, dict[str, float]],
) -> list[PlaceData]:
    """Order places by nearest-neighbor traversal."""
    if len(places) <= 1:
        return places

    ordered = []
    remaining = {p.id: p for p in places}

    current = max(places, key=lambda p: p.rating)
    ordered.append(current)
    del remaining[current.id]

    while remaining:
        nearest = None
        nearest_dist = float("inf")

        for place_id, place in remaining.items():
            dist = distance_matrix[current.id][place_id]
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = place

        if nearest:
            ordered.append(nearest)
            del remaining[nearest.id]
            current = nearest

    return ordered


def calculate_stop_duration(place: PlaceData, style: str) -> int:
    """Calculate stop duration based on style, category, and rating."""
    config = TRAVEL_STYLE_CONFIG[style]
    base_duration = config["base_duration_minutes"]

    if place.category == "ATTRACTION":
        duration = base_duration * config["attraction_multiplier"]
    elif place.category == "RESTAURANT":
        duration = base_duration * config["restaurant_multiplier"]
    else:
        duration = base_duration

    if place.rating >= 4.5:
        duration *= 1.2
    elif place.rating >= 4.0:
        duration *= 1.1

    return int(duration)


def generate_stop_reason(
    place: PlaceData,
    style: str,
    day_number: int,
    order_in_day: int,
    distance_from_previous: float,
) -> str:
    """Generate a human-readable explanation for including a stop."""
    reasons = []

    if place.rating >= 4.5:
        reasons.append(f"Highly rated ({place.rating}★)")
    elif place.rating >= 4.0:
        reasons.append(f"Well reviewed ({place.rating}★)")

    category_reasons = {
        "ATTRACTION": "Popular attraction",
        "RESTAURANT": "Recommended dining spot",
        "HOTEL": "Accommodation option",
    }
    reasons.append(category_reasons.get(place.category, "Point of interest"))

    if order_in_day > 1:
        if distance_from_previous < 1:
            reasons.append("Very close to previous stop")
        elif distance_from_previous < 3:
            reasons.append("Nearby previous stop")

    style_reasons = {
        "sightseeing": "fits fast-paced exploration",
        "relaxing": "allows leisurely enjoyment",
        "balanced": "good balance of time and experience",
    }
    reasons.append(style_reasons.get(style, ""))

    return ". ".join(filter(None, reasons)) + "."
