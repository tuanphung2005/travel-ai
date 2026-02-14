"""Service helpers for journey creation and AI planning orchestration."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from app.ai_planner import PlaceData
from app.models import AIDayPlan, AIStopSuggestion
from app.repositories import PlaceRepository


def parse_iso_datetime(value: datetime | str) -> datetime:
    """Ensure the input is a datetime object."""
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def create_initial_days(start_date: datetime, end_date: datetime) -> tuple[list[dict], int]:
    """Build an empty journey `days` payload between two dates (inclusive)."""
    total_days = (end_date.date() - start_date.date()).days + 1
    if total_days <= 0:
        raise ValueError("Journey must span at least 1 day")

    days = []
    for index in range(total_days):
        days.append({
            "day_number": index + 1,
            "date": start_date + timedelta(days=index),
            "stops": [],
        })

    return days, total_days


def map_day_plans_to_db(day_plans: list[dict]) -> list[dict]:
    """Convert planner output to MongoDB day format."""
    db_days = []
    for day_plan in day_plans:
        db_stops = [
            {
                "place_id": stop["place_id"],
                "place_name": stop["place_name"],
                "estimated_duration_minutes": stop["estimated_duration_minutes"],
                "reason": stop["reason"],
                "order": stop["order"],
                "latitude": stop["latitude"],
                "longitude": stop["longitude"],
                "category": stop["category"],
            }
            for stop in day_plan["stops"]
        ]
        db_days.append({
            "day_number": day_plan["day_number"],
            "date": day_plan["date"],
            "stops": db_stops,
        })
    return db_days


def map_day_plans_to_response(day_plans: list[dict]) -> list[AIDayPlan]:
    """Convert planner output to API response model objects."""
    response_days: list[AIDayPlan] = []
    for day_plan in day_plans:
        stops = [
            AIStopSuggestion(
                place_id=stop["place_id"],
                place_name=stop["place_name"],
                estimated_duration_minutes=stop["estimated_duration_minutes"],
                reason=stop["reason"],
                order=stop["order"],
                travel_time_from_previous_minutes=stop["travel_time_from_previous_minutes"],
                distance_from_previous_km=stop["distance_from_previous_km"],
                latitude=stop["latitude"],
                longitude=stop["longitude"],
                category=stop["category"],
                rating=stop["rating"],
            )
            for stop in day_plan["stops"]
        ]

        response_days.append(AIDayPlan(
            day_number=day_plan["day_number"],
            date=day_plan["date"],
            stops=stops,
            total_duration_minutes=day_plan["total_duration_minutes"],
            total_travel_time_minutes=day_plan["total_travel_time_minutes"],
            summary=day_plan["summary"],
        ))

    return response_days


async def select_related_place_docs(
    place_repo,
    seed_place_id: Optional[str],
    max_places: int,
) -> list[dict]:
    """Select related places using seed proximity/category and fallback top approved places."""
    seed_doc = None
    seed_tags: set[str] = set()
    candidate_docs: list[dict] = []

    if seed_place_id:
        seed_doc = await place_repo.get_by_id(seed_place_id)
        if not seed_doc:
            raise LookupError(f"Seed place with ID '{seed_place_id}' not found")

        seed_tags = {
            str(tag).strip().lower()
            for tag in seed_doc.get("tags", [])
            if str(tag).strip()
        }

        coords = seed_doc.get("location", {}).get("coordinates", [0, 0])
        if len(coords) >= 2:
            try:
                nearby_docs = await place_repo.search_nearby(
                    longitude=coords[0],
                    latitude=coords[1],
                    max_distance_meters=15000,
                )
                candidate_docs.extend(nearby_docs)
            except Exception:
                pass

        same_category_docs = await place_repo.get_by_category(
            seed_doc.get("category", "ATTRACTION"),
            limit=max_places * 3,
        )
        candidate_docs.extend(same_category_docs)

    candidate_docs.extend(await place_repo.get_all_approved(limit=max_places * 5))

    unique_candidates: dict[str, dict] = {}
    for doc in candidate_docs:
        if not doc:
            continue
        place_id = str(doc.get("_id", "")).strip()
        if not place_id:
            continue
        if doc.get("status") not in (None, "APPROVED"):
            continue
        unique_candidates[place_id] = doc

    if seed_doc:
        unique_candidates[str(seed_doc["_id"])] = seed_doc

    if not unique_candidates:
        raise ValueError("No approved places available to create a journey")

    def place_score(doc: dict) -> float:
        rating = float(doc.get("rating", 0.0) or 0.0)
        review_count = int(doc.get("reviewCount", 0) or 0)
        score = (rating * 12.0) + (min(review_count, 5000) / 250.0)

        if seed_doc and doc.get("category") == seed_doc.get("category"):
            score += 10.0

        if seed_tags:
            tags = {
                str(tag).strip().lower()
                for tag in doc.get("tags", [])
                if str(tag).strip()
            }
            score += float(len(seed_tags.intersection(tags)) * 3)

        return score

    ranked_docs = sorted(
        unique_candidates.values(),
        key=place_score,
        reverse=True,
    )

    selected_docs: list[dict] = []
    selected_ids: set[str] = set()

    if seed_doc:
        seed_id = str(seed_doc["_id"])
        selected_docs.append(seed_doc)
        selected_ids.add(seed_id)

    for doc in ranked_docs:
        place_id = str(doc["_id"])
        if place_id in selected_ids:
            continue
        selected_docs.append(doc)
        selected_ids.add(place_id)
        if len(selected_docs) >= max_places:
            break

    if not selected_docs:
        raise ValueError("Could not select places for the new journey")

    return selected_docs


def to_place_data_list(place_docs: list[dict]) -> list[PlaceData]:
    """Convert place documents into planner input objects."""
    return [PlaceRepository.to_place_data(doc) for doc in place_docs]
