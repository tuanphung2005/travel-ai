"""Core itinerary planner implementation."""
import math
import time
from datetime import datetime, timedelta
from typing import Optional

from app.planning_types import PlaceData
from app.services.weather_service import DailyWeather
from app.planning_utils import (
    TRAVEL_STYLE_CONFIG,
    AVERAGE_TRAVEL_SPEED_KMH,
    build_distance_matrix,
    blended_mood_score,
    optimize_route_order,
    route_distance_km,
    estimate_travel_time,
    calculate_stop_duration,
    generate_stop_reason,
    normalize_category,
    calculate_hotel_night_cost,
    calculate_place_score,
    weather_score_bonus,
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
        total_budget_vnd: int,
        daily_budget_vnd: int,
        mode: str,
        mood: Optional[str] = None,
        mood_distribution: Optional[dict[str, float]] = None,
        start_location: Optional[dict[str, float]] = None,
        max_places_per_day: int = 5,
        must_include_categories: Optional[list[str]] = None,
        exclude_categories: Optional[list[str]] = None,
        daily_weather: Optional[list[DailyWeather]] = None,
    ):
        self.places = places
        self.start_date = start_date
        self.end_date = end_date
        self.hours_per_day = hours_per_day
        self.travel_style = travel_style
        self.config = TRAVEL_STYLE_CONFIG[travel_style]
        self.total_budget_vnd = max(0, int(total_budget_vnd))
        self.daily_budget_vnd = max(0, int(daily_budget_vnd))
        self.mode = mode
        self.mood = mood
        self.mood_distribution = mood_distribution or {}
        self.start_location = start_location
        self.max_places_per_day = max(1, min(5, int(max_places_per_day)))
        self.must_include_categories = {c.upper() for c in (must_include_categories or [])}
        self.exclude_categories = {c.upper() for c in (exclude_categories or [])}
        self.daily_weather = daily_weather or []

        self.num_days = (end_date - start_date).days + 1
        self.distance_matrix = build_distance_matrix(places)
        self.planning_notes: list[str] = []
        self.candidate_pool_size = 0
        self.generation_time_ms = 0
        self.reason_codes: list[str] = []

        self.primary_hotel = None
        self.accommodation_cost_vnd = 0
        self.hotel_name = None
        self.num_nights = 0
        hotel_places = [p for p in self.places if normalize_category(p.category, p.tags) == "HOTEL"]
        if hotel_places:
            self.primary_hotel = max(hotel_places, key=lambda p: p.rating)

        if self.mode == "solo":
            selected_mood = self.mood or "NATURE_EXPLORE"
            self.mood_distribution = {selected_mood: 1.0}

        if self.daily_budget_vnd <= 0 and self.total_budget_vnd > 0 and self.num_days > 0:
            self.daily_budget_vnd = max(1, self.total_budget_vnd // self.num_days)

        if self.start_location is None and self.places:
            centroid_lat = sum(place.latitude for place in self.places) / len(self.places)
            centroid_lon = sum(place.longitude for place in self.places) / len(self.places)
            self.start_location = {
                "latitude": round(centroid_lat, 6),
                "longitude": round(centroid_lon, 6),
            }

    def _matches_category_filters(self, place: PlaceData) -> bool:
        normalized = normalize_category(place.category, place.tags)
        if self.exclude_categories and normalized in self.exclude_categories:
            return False

        name_lower = place.name.lower()
        excluded_phrases = [
            "công ty", "cong ty", "tnhh", "travel agency", 
            "phòng vé", "phong ve", "đại lý", "dai ly", 
            "nhà xe", "nha xe", "jsc"
        ]
        if any(phrase in name_lower for phrase in excluded_phrases):
            return False

        return True

    def _build_candidates(self, day_weather: Optional[DailyWeather] = None) -> list[tuple[PlaceData, float, dict[str, float]]]:
        filtered_places = [place for place in self.places if self._matches_category_filters(place)]
        
        # Exclude hotels from normal stops if they are handled as an anchor
        if self.primary_hotel:
            filtered_places = [p for p in filtered_places if normalize_category(p.category, p.tags) != "HOTEL"]

        if self.daily_budget_vnd > 0:
            within_budget = [
                place for place in filtered_places
                if place.estimated_cost_vnd <= self.daily_budget_vnd
            ]
        else:
            within_budget = filtered_places

        if "RESET_HEALING" in self.mood_distribution:
            healing_strict = [place for place in within_budget if place.healing_score >= 4 and place.crowd_level <= 3]
            if len(healing_strict) >= min(6, len(within_budget)):
                within_budget = healing_strict
            else:
                within_budget = [place for place in within_budget if place.healing_score >= 3 and place.crowd_level <= 4]
                self.planning_notes.append(
                    "RESET_HEALING fallback: expanded healing_score threshold to >=3 and crowd_level to <=4 due to limited pool."
                )
                self.reason_codes.append("not_enough_healing_gte4_low_crowd")

        scored: list[tuple[PlaceData, float, dict[str, float]]] = []
        for place in within_budget:
            mood_score, breakdown = blended_mood_score(place, self.mood_distribution)
            style_score = calculate_place_score(place, self.travel_style)
            
            # Combine them: 60% mood, 40% style
            final_score = round(mood_score * 0.6 + style_score * 0.4, 2)
            
            # Apply weather bonus if available
            if day_weather:
                w_bonus = weather_score_bonus(place, day_weather.condition)
                if w_bonus != 0:
                    final_score = round(final_score + w_bonus, 2)
                    breakdown[f"Weather ({day_weather.condition})"] = w_bonus

            scored.append((place, final_score, breakdown))

        scored.sort(
            key=lambda entry: (
                entry[1],                                           # final_score
                min(20, math.log10(max(1, entry[0].review_count))), # logarithmic review score instead of raw!
                entry[0].rating,                                    # rating
            ),
            reverse=True,
        )

        top_k = min(50, max(30, self.num_days * self.max_places_per_day * 6))
        top_candidates = scored[:top_k]
        self.candidate_pool_size = len(top_candidates)
        return top_candidates

    def _pick_places_for_day(
        self,
        candidates: list[tuple[PlaceData, float, dict[str, float]]],
        used_place_ids: set[str],
        day_budget_limit: int,
    ) -> list[tuple[PlaceData, float, dict[str, float]]]:
        available_minutes = int(self.hours_per_day * 60)
        selected: list[tuple[PlaceData, float, dict[str, float]]] = []
        category_counts: dict[str, int] = {}
        spent = 0
        consumed_minutes = 0

        unused = [entry for entry in candidates if entry[0].id not in used_place_ids]

        for required_category in self.must_include_categories:
            pick = None
            for entry in unused:
                cat = normalize_category(entry[0].category, entry[0].tags)
                if cat == required_category and entry[0].id not in {p[0].id for p in selected}:
                    pick = entry
                    break
            if pick is None:
                continue

            place = pick[0]
            projected_spent = spent + place.estimated_cost_vnd
            projected_minutes = consumed_minutes + calculate_stop_duration(place, self.travel_style)
            if projected_spent <= day_budget_limit and projected_minutes <= available_minutes:
                selected.append(pick)
                category_counts[required_category] = category_counts.get(required_category, 0) + 1
                spent = projected_spent
                consumed_minutes = projected_minutes

        if "CHILL_CAFE" in self.mood_distribution:
            cafe_pick = None
            for entry in unused:
                category = normalize_category(entry[0].category, entry[0].tags)
                if category == "CAFE" and entry[0].id not in {p[0].id for p in selected}:
                    cafe_pick = entry
                    break

            if cafe_pick:
                candidate_place = cafe_pick[0]
                projected_spent = spent + candidate_place.estimated_cost_vnd
                projected_minutes = consumed_minutes + calculate_stop_duration(candidate_place, self.travel_style)
                if projected_spent <= day_budget_limit and projected_minutes <= available_minutes:
                    selected.append(cafe_pick)
                    category_counts["CAFE"] = category_counts.get("CAFE", 0) + 1
                    spent = projected_spent
                    consumed_minutes = projected_minutes
                else:
                    self.reason_codes.append("chill_cafe_not_fit_budget_or_time")
            else:
                self.reason_codes.append("no_cafe_candidate_available")

        ranked = sorted(
            unused,
            key=lambda item: item[1] / max(1, item[0].estimated_cost_vnd),
            reverse=True,
        )

        for entry in ranked:
            if len(selected) >= self.max_places_per_day:
                break

            place = entry[0]
            if place.id in {p[0].id for p in selected}:
                continue

            category = normalize_category(place.category, place.tags)
            if category_counts.get(category, 0) >= 2:
                continue

            duration = calculate_stop_duration(place, self.travel_style)
            projected_spent = spent + place.estimated_cost_vnd
            projected_minutes = consumed_minutes + duration + self.config["buffer_time_minutes"]

            if projected_spent > day_budget_limit:
                continue
            if projected_minutes > available_minutes:
                continue

            selected.append(entry)
            category_counts[category] = category_counts.get(category, 0) + 1
            spent = projected_spent
            consumed_minutes = projected_minutes

        return selected

    def plan(self) -> list[dict]:
        """Generate the complete itinerary."""
        started_at = time.perf_counter()
        if not self.places:
            self.planning_notes.append("No places provided for planning.")
            return self._create_empty_days()

        self.planning_notes.append(
            f"Planning {len(self.places)} places over {self.num_days} days "
            f"with mood distribution {self.mood_distribution} and budget {self.daily_budget_vnd:,} VND/day."
        )

        day_plans = []
        used_place_ids: set[str] = set()
        total_spent = 0

        for day_idx in range(self.num_days):
            day_number = day_idx + 1
            day_date = self.start_date + timedelta(days=day_idx)
            
            day_weather = None
            if self.daily_weather:
                for w in self.daily_weather:
                    if w.date == day_date.date():
                        day_weather = w
                        break
            
            candidates = self._build_candidates(day_weather)
            if day_idx == 0:
                self.planning_notes.append(f"Candidate pool size after filtering/ranking: {self.candidate_pool_size}")
            
            if day_weather:
                self.planning_notes.append(f"Day {day_number} weather: {day_weather.condition} ({day_weather.description}).")

            if self.total_budget_vnd > 0:
                total_remaining = max(0, self.total_budget_vnd - total_spent)
                day_budget_limit = min(self.daily_budget_vnd, total_remaining) if self.daily_budget_vnd > 0 else total_remaining
            else:
                day_budget_limit = self.daily_budget_vnd

            if day_budget_limit <= 0 and self.total_budget_vnd > 0:
                self.reason_codes.append("total_budget_exhausted")
                day_budget_limit = 0

            selected = self._pick_places_for_day(candidates, used_place_ids, day_budget_limit)
            selected_places = [entry[0] for entry in selected]
            score_by_id = {entry[0].id: entry[1] for entry in selected}
            breakdown_by_id = {entry[0].id: entry[2] for entry in selected}

            if selected_places:
                optimized_places = optimize_route_order(
                    selected_places,
                    self.distance_matrix,
                    start_location={"latitude": self.primary_hotel.latitude, "longitude": self.primary_hotel.longitude} if self.primary_hotel else self.start_location,
                    two_opt_enabled=True,
                )
            else:
                optimized_places = []

            stops = []
            total_duration = 0
            total_travel_time = 0
            total_estimated_cost_vnd = 0
            previous_place: Optional[PlaceData] = None
            day_explanations: list[str] = []

            places_to_visit = list(optimized_places)
            if self.primary_hotel:
                places_to_visit.insert(0, self.primary_hotel)
                if len(places_to_visit) > 1:
                    places_to_visit.append(self.primary_hotel)

            for order, place in enumerate(places_to_visit, 1):
                if previous_place:
                    distance = self.distance_matrix[previous_place.id][place.id]
                    travel_time = estimate_travel_time(distance)
                else:
                    distance = 0.0
                    travel_time = 0

                is_hotel_anchor = self.primary_hotel and place.id == self.primary_hotel.id and (order == 1 or order == len(places_to_visit))

                if is_hotel_anchor:
                    if order == 1:
                        duration = 30
                        reason = "Good morning! Start your day from the hotel."
                    else:
                        duration = 0
                        reason = "Time to rest. Return to the hotel."
                    cost = 0
                else:
                    duration = calculate_stop_duration(place, self.travel_style)
                    w_cond = f" ({day_weather.condition})" if day_weather else ""
                    reason = generate_stop_reason(
                        place,
                        self.travel_style,
                        day_number,
                        order,
                        distance,
                        mood_label=", ".join(self.mood_distribution.keys()) + w_cond,
                        final_score=score_by_id.get(place.id, 0.0),
                    )
                    cost = place.estimated_cost_vnd

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
                    "estimated_cost_vnd": cost,
                    "final_score": score_by_id.get(place.id, 0.0),
                    "mood_score_breakdown": breakdown_by_id.get(place.id, {}),
                    "is_hotel_anchor": bool(is_hotel_anchor),
                })

                total_duration += duration
                total_travel_time += travel_time
                total_estimated_cost_vnd += cost
                previous_place = place
                used_place_ids.add(place.id)

            total_distance = route_distance_km(places_to_visit, self.distance_matrix)
            total_spent += total_estimated_cost_vnd
            effective_day_budget = day_budget_limit if day_budget_limit > 0 else self.daily_budget_vnd
            remaining_today = max(0, effective_day_budget - total_estimated_cost_vnd)
            day_explanations.append(
                f"Spent {total_estimated_cost_vnd:,} VND; remaining {remaining_today:,} VND."
            )
            if "RESET_HEALING" in self.mood_distribution and stops:
                healing_ratio = sum(
                    1 for p in optimized_places if p.healing_score >= 4
                ) / len(optimized_places)
                day_explanations.append(
                    f"RESET_HEALING quality: {round(healing_ratio * 100)}% stops with healing_score >= 4."
                )
                if healing_ratio < 0.6:
                    self.reason_codes.append("reset_healing_ratio_below_60")

            if stops:
                summary = (
                    f"Day {day_number}: {len(stops)} stops, "
                    f"{total_duration} mins visiting, "
                    f"{total_travel_time} mins traveling, "
                    f"{total_distance} km route, {total_estimated_cost_vnd:,} VND."
                )
            else:
                summary = f"Day {day_number}: Free day for personal exploration."

            day_dict = {
                "day_number": day_number,
                "date": day_date,
                "stops": stops,
                "total_duration_minutes": total_duration,
                "total_travel_time_minutes": total_travel_time,
                "total_estimated_cost_vnd": total_estimated_cost_vnd,
                "total_distance_km": total_distance,
                "spent_today": total_estimated_cost_vnd,
                "remaining_today": remaining_today,
                "saved_vs_budget": remaining_today,
                "explanations": day_explanations,
                "summary": summary,
            }
            if day_weather:
                day_dict["weather"] = {
                    "condition": day_weather.condition,
                    "description": day_weather.description,
                    "temp_min_c": day_weather.temp_min_c,
                    "temp_max_c": day_weather.temp_max_c,
                    "rain_probability": day_weather.rain_probability,
                    "icon": day_weather.icon,
                }
            day_plans.append(day_dict)

        self.planning_notes.append(
            f"Planning complete. Total stops: {sum(len(d['stops']) for d in day_plans)}"
        )
        
        num_nights = max(0, self.num_days - 1)
        accommodation_cost_vnd = 0
        hotel_name = None
        
        self.num_nights = num_nights
        
        if self.primary_hotel:
            hotel_name = self.primary_hotel.name
            accommodation_cost_vnd = calculate_hotel_night_cost(self.primary_hotel, num_nights)
            
            self.hotel_name = hotel_name
            self.accommodation_cost_vnd = accommodation_cost_vnd
            
            self.planning_notes.append(f"Accommodation cost: {accommodation_cost_vnd:,} VND ({num_nights} nights at {hotel_name})")
            total_spent += accommodation_cost_vnd
            
        if self.total_budget_vnd > 0:
            self.planning_notes.append(
                f"Total spent estimate: {total_spent:,} VND. Savings vs total budget: {max(0, self.total_budget_vnd - total_spent):,} VND."
            )

        self.generation_time_ms = int((time.perf_counter() - started_at) * 1000)
        self.planning_notes.append(f"generation_time_ms={self.generation_time_ms}")
        if self.reason_codes:
            unique_codes = sorted(set(self.reason_codes))
            self.planning_notes.append(f"reason_codes={unique_codes}")

        self.candidate_places_details = []
        for entry in candidates:
            place = entry[0]
            self.candidate_places_details.append({
                "place_id": place.id,
                "place_name": place.name,
                "category": place.category,
                "rating": place.rating,
                "estimated_cost_vnd": place.estimated_cost_vnd,
                "final_score": entry[1],
                "mood_score_breakdown": entry[2],
                "selected": place.id in used_place_ids,
            })

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
                "total_estimated_cost_vnd": 0,
                "total_distance_km": 0.0,
                "spent_today": 0,
                "remaining_today": self.daily_budget_vnd,
                "saved_vs_budget": self.daily_budget_vnd,
                "explanations": ["No feasible places within constraints."],
            }
            for i in range(self.num_days)
        ]

    def get_explanation(self) -> dict:
        """Get detailed explanation of the planning algorithm."""
        return {
            "algorithm_description": (
                "This itinerary was generated using a deterministic planning algorithm "
                "that applies mood-based scoring, budget-constrained greedy packing, "
                "and route optimization with nearest-neighbor + 2-opt refinement."
            ),
            "distance_calculation": (
                "Distances between places are calculated using the Haversine formula, "
                "which computes great-circle distance on Earth's surface. "
                f"Average travel speed assumed: {AVERAGE_TRAVEL_SPEED_KMH} km/h."
            ),
            "grouping_strategy": (
                "Places are selected day-by-day from a global candidate pool while enforcing "
                "budget, per-day stop cap, and category diversity constraints."
            ),
            "style_adjustments": {
                "current_style": self.travel_style,
                "config": self.config,
                "explanation": TRAVEL_STYLE_CONFIG[self.travel_style]["description"],
            },
            "constraints_applied": [
                f"Maximum {self.max_places_per_day} stops per day",
                f"Available time: {self.hours_per_day} hours/day",
                f"Daily budget cap: {self.daily_budget_vnd:,} VND",
                f"Buffer time between stops: {self.config['buffer_time_minutes']} minutes",
            ],
            "place_selection_criteria": [
                "Mood score: weighted by selected mood or group mood distribution",
                "Budget fit: only places with feasible cost are considered",
                "Selection utility: greedy by score/cost ratio",
                "Category diversity: no more than 2 stops in same category/day",
            ],
        }
