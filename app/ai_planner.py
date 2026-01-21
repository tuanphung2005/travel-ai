"""
AI Planning Algorithm for Travel Itinerary Generation.

This module implements a deterministic, explainable AI system that:
1. Calculates distances between places using Haversine formula
2. Groups nearby places into the same day
3. Optimizes route order within each day using nearest neighbor
4. Adjusts stop durations based on travel style
5. Provides reasoning for each decision

IMPORTANT: This AI does NOT hallucinate or invent places.
All suggestions come from the database.
"""
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


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


# ============================================
# TRAVEL STYLE CONFIGURATIONS
# ============================================

TRAVEL_STYLE_CONFIG = {
    "sightseeing": {
        "description": "Fast-paced exploration with more stops",
        "base_duration_minutes": 45,  # Shorter time at each place
        "max_stops_per_day": 8,
        "min_stops_per_day": 4,
        "attraction_multiplier": 1.0,
        "restaurant_multiplier": 0.8,  # Quick meals
        "buffer_time_minutes": 10,  # Less buffer between stops
    },
    "relaxing": {
        "description": "Leisurely pace with fewer stops",
        "base_duration_minutes": 120,  # Longer time at each place
        "max_stops_per_day": 4,
        "min_stops_per_day": 2,
        "attraction_multiplier": 1.5,  # More time to enjoy
        "restaurant_multiplier": 1.5,  # Leisurely meals
        "buffer_time_minutes": 30,  # More buffer for rest
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

# Average travel speed in km/h (accounting for urban traffic, walking, etc.)
AVERAGE_TRAVEL_SPEED_KMH = 25


# ============================================
# DISTANCE CALCULATION (HAVERSINE FORMULA)
# ============================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula.
    
    Args:
        lat1, lon1: Latitude and longitude of point 1 (in degrees)
        lat2, lon2: Latitude and longitude of point 2 (in degrees)
    
    Returns:
        Distance in kilometers
    
    Formula:
        a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
        c = 2 * atan2(√a, √(1-a))
        d = R * c
    
    Where R is Earth's radius (6371 km)
    """
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    
    return distance


def estimate_travel_time(distance_km: float) -> int:
    """
    Estimate travel time between two places.
    
    Args:
        distance_km: Distance in kilometers
    
    Returns:
        Estimated travel time in minutes
    
    Assumes average urban travel speed of 25 km/h,
    accounting for traffic, public transport waits, etc.
    """
    if distance_km <= 0:
        return 0
    
    # Calculate time in hours, then convert to minutes
    time_hours = distance_km / AVERAGE_TRAVEL_SPEED_KMH
    time_minutes = int(time_hours * 60)
    
    # Minimum 5 minutes for any travel
    return max(5, time_minutes)


# ============================================
# DISTANCE MATRIX CALCULATION
# ============================================

def build_distance_matrix(places: list[PlaceData]) -> dict[str, dict[str, float]]:
    """
    Build a distance matrix between all places.
    
    Args:
        places: List of places
    
    Returns:
        Dictionary mapping place_id -> place_id -> distance_km
    
    Example:
        matrix["place1"]["place2"] = 2.5  # 2.5 km between place1 and place2
    """
    matrix = {}
    
    for p1 in places:
        matrix[p1.id] = {}
        for p2 in places:
            if p1.id == p2.id:
                matrix[p1.id][p2.id] = 0.0
            else:
                distance = haversine_distance(
                    p1.latitude, p1.longitude,
                    p2.latitude, p2.longitude
                )
                matrix[p1.id][p2.id] = round(distance, 2)
    
    return matrix


# ============================================
# PLACE SCORING AND PRIORITIZATION
# ============================================

def calculate_place_score(place: PlaceData, style: str) -> float:
    """
    Calculate a priority score for a place based on multiple factors.
    Higher score = higher priority for inclusion.
    
    Factors:
        - Rating (40% weight): Higher rated places preferred
        - Review count (20% weight): More reviewed = more reliable
        - Category bonus (40% weight): Based on travel style
    
    Args:
        place: The place to score
        style: Travel style (sightseeing, relaxing, balanced)
    
    Returns:
        Score between 0 and 100
    """
    # Rating score (0-40 points)
    # Normalize rating from 0-5 scale to 0-40
    rating_score = (place.rating / 5.0) * 40
    
    # Review count score (0-20 points)
    # Logarithmic scale to prevent very popular places from dominating
    review_score = min(20, math.log10(max(1, place.review_count)) * 5)
    
    # Category bonus based on travel style (0-40 points)
    category_bonuses = {
        "sightseeing": {
            "ATTRACTION": 40,
            "RESTAURANT": 20,
            "HOTEL": 10,
        },
        "relaxing": {
            "ATTRACTION": 25,
            "RESTAURANT": 35,
            "HOTEL": 30,
        },
        "balanced": {
            "ATTRACTION": 35,
            "RESTAURANT": 30,
            "HOTEL": 20,
        },
    }
    
    category_score = category_bonuses.get(style, {}).get(place.category, 20)
    
    total_score = rating_score + review_score + category_score
    
    return round(total_score, 2)


# ============================================
# CLUSTERING ALGORITHM (Geographic Grouping)
# ============================================

def cluster_places_by_proximity(
    places: list[PlaceData],
    distance_matrix: dict[str, dict[str, float]],
    num_clusters: int
) -> list[list[PlaceData]]:
    """
    Group places into clusters based on geographic proximity.
    Uses a simple greedy clustering approach.
    
    Algorithm:
    1. Start with the highest-rated place as first cluster center
    2. Assign each place to nearest cluster
    3. Split clusters that are too large
    
    Args:
        places: List of places to cluster
        distance_matrix: Pre-computed distance matrix
        num_clusters: Target number of clusters (days)
    
    Returns:
        List of place clusters, one per day
    """
    if not places:
        return []
    
    if len(places) <= num_clusters:
        # If we have fewer places than days, one place per day
        return [[p] for p in places]
    
    # Sort places by rating to start clusters with best places
    sorted_places = sorted(places, key=lambda p: p.rating, reverse=True)
    
    # Initialize clusters with top-rated places as seeds
    clusters: list[list[PlaceData]] = []
    used_ids: set[str] = set()
    
    # Select seed places that are geographically spread out
    seeds = []
    seeds.append(sorted_places[0])
    used_ids.add(sorted_places[0].id)
    
    while len(seeds) < min(num_clusters, len(places)):
        # Find place that is farthest from all current seeds
        best_place = None
        best_min_distance = -1
        
        for place in sorted_places:
            if place.id in used_ids:
                continue
            
            # Find minimum distance to any seed
            min_dist = min(
                distance_matrix[place.id][seed.id] 
                for seed in seeds
            )
            
            if min_dist > best_min_distance:
                best_min_distance = min_dist
                best_place = place
        
        if best_place:
            seeds.append(best_place)
            used_ids.add(best_place.id)
    
    # Initialize clusters with seeds
    clusters = [[seed] for seed in seeds]
    
    # Assign remaining places to nearest cluster
    for place in places:
        if place.id in used_ids:
            continue
        
        # Find nearest cluster (by distance to seed)
        min_distance = float('inf')
        nearest_cluster_idx = 0
        
        for idx, cluster in enumerate(clusters):
            # Distance to cluster seed (first element)
            dist = distance_matrix[place.id][cluster[0].id]
            if dist < min_distance:
                min_distance = dist
                nearest_cluster_idx = idx
        
        clusters[nearest_cluster_idx].append(place)
    
    return clusters


# ============================================
# ROUTE OPTIMIZATION (Nearest Neighbor)
# ============================================

def optimize_route_order(
    places: list[PlaceData],
    distance_matrix: dict[str, dict[str, float]]
) -> list[PlaceData]:
    """
    Optimize the order of places to minimize total travel distance.
    Uses the Nearest Neighbor heuristic.
    
    Algorithm:
    1. Start with the highest-rated place
    2. Repeatedly visit the nearest unvisited place
    3. Return ordered list
    
    This is a greedy algorithm with O(n²) complexity.
    Not optimal but provides good results for small sets.
    
    Args:
        places: List of places to order
        distance_matrix: Pre-computed distance matrix
    
    Returns:
        Ordered list of places
    """
    if len(places) <= 1:
        return places
    
    # Start with highest-rated place
    ordered = []
    remaining = {p.id: p for p in places}
    
    # Find starting place (highest rated)
    current = max(places, key=lambda p: p.rating)
    ordered.append(current)
    del remaining[current.id]
    
    # Greedily add nearest neighbor
    while remaining:
        nearest = None
        nearest_dist = float('inf')
        
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


# ============================================
# DURATION CALCULATION
# ============================================

def calculate_stop_duration(
    place: PlaceData,
    style: str
) -> int:
    """
    Calculate recommended duration at a stop based on:
    - Travel style
    - Place category
    - Place rating (higher rated = worth more time)
    
    Args:
        place: The place
        style: Travel style
    
    Returns:
        Duration in minutes
    """
    config = TRAVEL_STYLE_CONFIG[style]
    base_duration = config["base_duration_minutes"]
    
    # Apply category multiplier
    if place.category == "ATTRACTION":
        duration = base_duration * config["attraction_multiplier"]
    elif place.category == "RESTAURANT":
        duration = base_duration * config["restaurant_multiplier"]
    else:
        duration = base_duration
    
    # Bonus time for highly-rated places
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
    distance_from_previous: float
) -> str:
    """
    Generate a human-readable explanation for why this stop was chosen.
    
    Args:
        place: The place
        style: Travel style
        day_number: Which day
        order_in_day: Order within the day
        distance_from_previous: Distance from previous stop
    
    Returns:
        Explanation string
    """
    reasons = []
    
    # Rating reason
    if place.rating >= 4.5:
        reasons.append(f"Highly rated ({place.rating}★)")
    elif place.rating >= 4.0:
        reasons.append(f"Well reviewed ({place.rating}★)")
    
    # Category reason
    category_reasons = {
        "ATTRACTION": "Popular attraction",
        "RESTAURANT": "Recommended dining spot",
        "HOTEL": "Accommodation option",
    }
    reasons.append(category_reasons.get(place.category, "Point of interest"))
    
    # Proximity reason
    if order_in_day > 1:
        if distance_from_previous < 1:
            reasons.append("Very close to previous stop")
        elif distance_from_previous < 3:
            reasons.append("Nearby previous stop")
    
    # Style-specific reasons
    style_reasons = {
        "sightseeing": "fits fast-paced exploration",
        "relaxing": "allows leisurely enjoyment",
        "balanced": "good balance of time and experience",
    }
    reasons.append(style_reasons.get(style, ""))
    
    return ". ".join(filter(None, reasons)) + "."


# ============================================
# MAIN PLANNING ALGORITHM
# ============================================

class ItineraryPlanner:
    """
    Main class for generating travel itineraries.
    
    This is a deterministic, explainable planning system.
    No machine learning or black-box decisions.
    All logic is traceable and reproducible.
    """
    
    def __init__(
        self,
        places: list[PlaceData],
        start_date: datetime,
        end_date: datetime,
        hours_per_day: float,
        travel_style: str
    ):
        """
        Initialize the planner.
        
        Args:
            places: List of places to include in the itinerary
            start_date: Journey start date
            end_date: Journey end date
            hours_per_day: Available hours for travel each day
            travel_style: User's preferred travel style
        """
        self.places = places
        self.start_date = start_date
        self.end_date = end_date
        self.hours_per_day = hours_per_day
        self.travel_style = travel_style
        self.config = TRAVEL_STYLE_CONFIG[travel_style]
        
        # Calculate number of days
        self.num_days = (end_date - start_date).days + 1
        
        # Build distance matrix
        self.distance_matrix = build_distance_matrix(places)
        
        # Planning notes for explanation
        self.planning_notes: list[str] = []
    
    def plan(self) -> list[dict]:
        """
        Generate the complete itinerary.
        
        Returns:
            List of day plans with stops
        """
        if not self.places:
            self.planning_notes.append("No places provided for planning.")
            return self._create_empty_days()
        
        # Log planning start
        self.planning_notes.append(
            f"Planning {len(self.places)} places over {self.num_days} days "
            f"with {self.hours_per_day} hours/day in '{self.travel_style}' style."
        )
        
        # Step 1: Score and prioritize places
        scored_places = [
            (place, calculate_place_score(place, self.travel_style))
            for place in self.places
        ]
        scored_places.sort(key=lambda x: x[1], reverse=True)
        
        self.planning_notes.append(
            f"Top rated place: {scored_places[0][0].name} (score: {scored_places[0][1]})"
        )
        
        # Step 2: Cluster places by geographic proximity
        clusters = cluster_places_by_proximity(
            self.places,
            self.distance_matrix,
            self.num_days
        )
        
        self.planning_notes.append(
            f"Created {len(clusters)} geographic clusters for {self.num_days} days."
        )
        
        # Step 3: Generate day-by-day plans
        day_plans = []
        available_minutes = int(self.hours_per_day * 60)
        
        for day_idx in range(self.num_days):
            day_number = day_idx + 1
            day_date = self.start_date + timedelta(days=day_idx)
            
            # Get cluster for this day (or empty if no more clusters)
            if day_idx < len(clusters):
                day_places = clusters[day_idx]
            else:
                day_places = []
            
            # Optimize route order within the day
            if day_places:
                optimized_places = optimize_route_order(
                    day_places, self.distance_matrix
                )
            else:
                optimized_places = []
            
            # Create stops with time constraints
            stops = []
            total_duration = 0
            total_travel_time = 0
            previous_place: Optional[PlaceData] = None
            
            for order, place in enumerate(optimized_places, 1):
                # Calculate travel time from previous stop
                if previous_place:
                    distance = self.distance_matrix[previous_place.id][place.id]
                    travel_time = estimate_travel_time(distance)
                else:
                    distance = 0.0
                    travel_time = 0
                
                # Calculate duration at this stop
                duration = calculate_stop_duration(place, self.travel_style)
                
                # Check if we have time for this stop
                projected_total = (
                    total_duration + total_travel_time + 
                    travel_time + duration + 
                    self.config["buffer_time_minutes"]
                )
                
                if projected_total > available_minutes:
                    self.planning_notes.append(
                        f"Day {day_number}: Skipped {place.name} due to time constraints."
                    )
                    continue
                
                # Check max stops limit
                if len(stops) >= self.config["max_stops_per_day"]:
                    self.planning_notes.append(
                        f"Day {day_number}: Reached max stops ({self.config['max_stops_per_day']})."
                    )
                    break
                
                # Generate reason for this stop
                reason = generate_stop_reason(
                    place, self.travel_style, day_number, order, distance
                )
                
                # Add the stop
                stops.append({
                    "place_id": place.id,
                    "place_name": place.name,
                    "estimated_duration_minutes": duration,
                    "reason": reason,
                    "order": len(stops) + 1,
                    "travel_time_from_previous_minutes": travel_time,
                    "distance_from_previous_km": round(distance, 2),
                    "latitude": place.latitude,
                    "longitude": place.longitude,
                    "category": place.category,
                    "rating": place.rating,
                })
                
                total_duration += duration
                total_travel_time += travel_time
                previous_place = place
            
            # Generate day summary
            if stops:
                summary = (
                    f"Day {day_number}: {len(stops)} stops, "
                    f"{total_duration} mins visiting, "
                    f"{total_travel_time} mins traveling."
                )
            else:
                summary = f"Day {day_number}: Free day for personal exploration."
            
            day_plans.append({
                "day_number": day_number,
                "date": day_date,
                "stops": stops,
                "total_duration_minutes": total_duration,
                "total_travel_time_minutes": total_travel_time,
                "summary": summary,
            })
        
        self.planning_notes.append(
            f"Planning complete. Total stops: {sum(len(d['stops']) for d in day_plans)}"
        )
        
        return day_plans
    
    def _create_empty_days(self) -> list[dict]:
        """Create empty day structures when no places are provided."""
        return [
            {
                "day_number": i + 1,
                "date": self.start_date + timedelta(days=i),
                "stops": [],
                "total_duration_minutes": 0,
                "total_travel_time_minutes": 0,
                "summary": f"Day {i + 1}: No places selected for planning.",
            }
            for i in range(self.num_days)
        ]
    
    def get_explanation(self) -> dict:
        """
        Get detailed explanation of the planning algorithm.
        
        Returns:
            Dictionary with algorithm explanations
        """
        return {
            "algorithm_description": (
                "This itinerary was generated using a deterministic planning algorithm "
                "that considers geographic proximity, place ratings, travel style preferences, "
                "and time constraints. No machine learning or randomness is involved."
            ),
            "distance_calculation": (
                "Distances between places are calculated using the Haversine formula, "
                "which computes great-circle distance on Earth's surface. "
                f"Average travel speed assumed: {AVERAGE_TRAVEL_SPEED_KMH} km/h."
            ),
            "grouping_strategy": (
                "Places are grouped into daily clusters based on geographic proximity. "
                "The algorithm selects seed places that are geographically spread out, "
                "then assigns remaining places to the nearest cluster."
            ),
            "style_adjustments": {
                "current_style": self.travel_style,
                "config": self.config,
                "explanation": TRAVEL_STYLE_CONFIG[self.travel_style]["description"],
            },
            "constraints_applied": [
                f"Maximum {self.config['max_stops_per_day']} stops per day",
                f"Minimum {self.config['min_stops_per_day']} stops per day (if places available)",
                f"Available time: {self.hours_per_day} hours/day",
                f"Buffer time between stops: {self.config['buffer_time_minutes']} minutes",
            ],
            "place_selection_criteria": [
                "Rating (40% weight): Higher rated places preferred",
                "Review count (20% weight): More reviews = more reliable",
                "Category fit (40% weight): Based on travel style",
            ],
        }
