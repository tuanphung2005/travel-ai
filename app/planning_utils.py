"""Pure planning utilities used by the itinerary planner."""
import math
from typing import Optional

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

MOOD_CATEGORY_BONUS = {
    "RESET_HEALING": {
        "PARK": 35,
        "NATURE": 35,
        "SPA": 30,
        "WELLNESS": 30,
        "ATTRACTION": 12,
    },
    "CHILL_CAFE": {
        "CAFE": 40,
        "TEAHOUSE": 35,
        "BAKERY": 25,
        "RESTAURANT": 20,
    },
    "NATURE_EXPLORE": {
        "NATURE": 40,
        "PARK": 35,
        "ATTRACTION": 20,
    },
    "FOOD_LOCAL": {
        "FOOD": 40,
        "RESTAURANT": 35,
        "STREET_FOOD": 35,
        "MARKET": 25,
    },
}


def normalize_category(raw_category: str, tags: list[str]) -> str:
    """Normalize category into richer category labels for mood matching."""
    base = str(raw_category or "").strip().upper()
    normalized_tags = {str(tag).strip().lower() for tag in tags if str(tag).strip()}

    if "cafe" in normalized_tags or "coffee" in normalized_tags:
        return "CAFE"
    if "tea" in normalized_tags or "teahouse" in normalized_tags:
        return "TEAHOUSE"
    if "park" in normalized_tags:
        return "PARK"
    if "nature" in normalized_tags or "lake" in normalized_tags or "garden" in normalized_tags:
        return "NATURE"
    if "street food" in normalized_tags or "street_food" in normalized_tags:
        return "STREET_FOOD"
    if "market" in normalized_tags:
        return "MARKET"
    if "spa" in normalized_tags or "wellness" in normalized_tags:
        return "SPA"

    return base or "ATTRACTION"


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


def mood_score(place: PlaceData, mood: str) -> float:
    """Calculate mood affinity score for one place on a 0..100 scale."""
    rating_score = (max(0.0, min(place.rating, 5.0)) / 5.0) * 20
    category = normalize_category(place.category, place.tags)
    category_bonus = MOOD_CATEGORY_BONUS.get(mood, {}).get(category, 5)
    score = rating_score + category_bonus

    if mood == "RESET_HEALING":
        score += max(0, min(place.healing_score, 5)) * 8
        score -= max(0, min(place.crowd_level, 5)) * 5

    return round(max(0.0, min(score, 100.0)), 2)


def blended_mood_score(
    place: PlaceData,
    mood_distribution: dict[str, float],
) -> tuple[float, dict[str, float]]:
    """Compute weighted mood score and provide per-mood breakdown."""
    breakdown: dict[str, float] = {}
    total = 0.0
    normalized_sum = sum(mood_distribution.values()) or 1.0

    for mood, weight in mood_distribution.items():
        normalized_weight = max(0.0, weight) / normalized_sum
        score = mood_score(place, mood)
        breakdown[mood] = score
        total += normalized_weight * score

    return round(total, 2), breakdown


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
    start_location: Optional[dict[str, float]] = None,
    two_opt_enabled: bool = True,
) -> list[PlaceData]:
    """Order places by nearest-neighbor traversal and optional 2-opt improvement."""
    if len(places) <= 1:
        return places

    ordered = []
    remaining = {p.id: p for p in places}

    if start_location and "latitude" in start_location and "longitude" in start_location:
        start_lat = float(start_location["latitude"])
        start_lon = float(start_location["longitude"])
        current = min(
            places,
            key=lambda p: haversine_distance(start_lat, start_lon, p.latitude, p.longitude),
        )
    else:
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

    if two_opt_enabled and len(ordered) >= 4:
        ordered = two_opt_route(ordered, distance_matrix)

    return ordered


def route_distance_km(route: list[PlaceData], matrix: dict[str, dict[str, float]]) -> float:
    """Return total route distance in km."""
    if len(route) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(route)):
        total += matrix[route[i - 1].id][route[i].id]
    return round(total, 2)


def two_opt_route(
    route: list[PlaceData],
    distance_matrix: dict[str, dict[str, float]],
) -> list[PlaceData]:
    """Apply 2-opt local search to improve route distance."""
    improved = route[:]
    best_distance = route_distance_km(improved, distance_matrix)
    if len(improved) < 4:
        return improved

    changed = True
    while changed:
        changed = False
        for i in range(1, len(improved) - 2):
            for j in range(i + 1, len(improved) - 1):
                candidate = improved[:i] + list(reversed(improved[i:j + 1])) + improved[j + 1:]
                candidate_distance = route_distance_km(candidate, distance_matrix)
                if candidate_distance + 0.01 < best_distance:
                    improved = candidate
                    best_distance = candidate_distance
                    changed = True
        if changed:
            continue
    return improved


def calculate_stop_duration(place: PlaceData, style: str) -> int:
    """Calculate stop duration based on style, category, and rating."""
    config = TRAVEL_STYLE_CONFIG.get(style, TRAVEL_STYLE_CONFIG["balanced"])
    base_duration = max(30, int(place.avg_visit_duration_min or config["base_duration_minutes"]))
    category = normalize_category(place.category, place.tags)

    if category in {"ATTRACTION", "NATURE", "PARK"}:
        duration = base_duration * config["attraction_multiplier"]
    elif category in {"RESTAURANT", "FOOD", "CAFE", "STREET_FOOD"}:
        duration = base_duration * config["restaurant_multiplier"]
    else:
        duration = base_duration

    return int(max(30, duration))


def generate_stop_reason(
    place: PlaceData,
    style: str,
    day_number: int,
    order_in_day: int,
    distance_from_previous: float,
    mood_label: str,
    final_score: float,
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
    reasons.append(f"aligned with mood {mood_label} (score {final_score})")

    return ". ".join(filter(None, reasons)) + "."
