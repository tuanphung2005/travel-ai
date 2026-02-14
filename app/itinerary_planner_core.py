"""Core itinerary planner implementation."""
from datetime import datetime, timedelta
from typing import Optional

from app.planning_types import PlaceData
from app.planning_utils import (
    TRAVEL_STYLE_CONFIG,
    AVERAGE_TRAVEL_SPEED_KMH,
    build_distance_matrix,
    calculate_place_score,
    cluster_places_by_proximity,
    optimize_route_order,
    estimate_travel_time,
    calculate_stop_duration,
    generate_stop_reason,
)


class ItineraryPlanner:
    """Main class for generating deterministic travel itineraries."""

    def __init__(
        self,
        places: list[PlaceData],
        start_date: datetime,
        end_date: datetime,
        hours_per_day: float,
        travel_style: str,
    ):
        self.places = places
        self.start_date = start_date
        self.end_date = end_date
        self.hours_per_day = hours_per_day
        self.travel_style = travel_style
        self.config = TRAVEL_STYLE_CONFIG[travel_style]

        self.num_days = (end_date - start_date).days + 1
        self.distance_matrix = build_distance_matrix(places)
        self.planning_notes: list[str] = []

    def plan(self) -> list[dict]:
        """Generate the complete itinerary."""
        if not self.places:
            self.planning_notes.append("No places provided for planning.")
            return self._create_empty_days()

        self.planning_notes.append(
            f"Planning {len(self.places)} places over {self.num_days} days "
            f"with {self.hours_per_day} hours/day in '{self.travel_style}' style."
        )

        scored_places = [
            (place, calculate_place_score(place, self.travel_style))
            for place in self.places
        ]
        scored_places.sort(key=lambda x: x[1], reverse=True)

        self.planning_notes.append(
            f"Top rated place: {scored_places[0][0].name} (score: {scored_places[0][1]})"
        )

        clusters = cluster_places_by_proximity(
            self.places,
            self.distance_matrix,
            self.num_days,
        )

        self.planning_notes.append(
            f"Created {len(clusters)} geographic clusters for {self.num_days} days."
        )

        day_plans = []
        available_minutes = int(self.hours_per_day * 60)

        for day_idx in range(self.num_days):
            day_number = day_idx + 1
            day_date = self.start_date + timedelta(days=day_idx)

            if day_idx < len(clusters):
                day_places = clusters[day_idx]
            else:
                day_places = []

            if day_places:
                optimized_places = optimize_route_order(day_places, self.distance_matrix)
            else:
                optimized_places = []

            stops = []
            total_duration = 0
            total_travel_time = 0
            previous_place: Optional[PlaceData] = None

            for order, place in enumerate(optimized_places, 1):
                if previous_place:
                    distance = self.distance_matrix[previous_place.id][place.id]
                    travel_time = estimate_travel_time(distance)
                else:
                    distance = 0.0
                    travel_time = 0

                duration = calculate_stop_duration(place, self.travel_style)

                projected_total = (
                    total_duration
                    + total_travel_time
                    + travel_time
                    + duration
                    + self.config["buffer_time_minutes"]
                )

                if projected_total > available_minutes:
                    self.planning_notes.append(
                        f"Day {day_number}: Skipped {place.name} due to time constraints."
                    )
                    continue

                if len(stops) >= self.config["max_stops_per_day"]:
                    self.planning_notes.append(
                        f"Day {day_number}: Reached max stops ({self.config['max_stops_per_day']})."
                    )
                    break

                reason = generate_stop_reason(
                    place,
                    self.travel_style,
                    day_number,
                    order,
                    distance,
                )

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
        """Get detailed explanation of the planning algorithm."""
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
