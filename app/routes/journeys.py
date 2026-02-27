"""
API Routes for Journey and AI Planning endpoints.
"""
from fastapi import APIRouter, HTTPException, status
from datetime import datetime

from app.models import (
    AIPlanRequest,
    AIPlanResponse,
    AIExplanation,
    CreateJourneyFromRelatedRequest,
    CreateJourneyFromRelatedResponse,
)
from app.repositories import (
    get_journey_repository,
    get_place_repository,
)
from app.ai_planner import ItineraryPlanner
from app.planning_types import PlaceData
from app.planning_utils import optimize_route_order, build_distance_matrix, estimate_travel_time
from app.services.journey_planning import (
    parse_iso_datetime,
    create_initial_days,
    map_day_plans_to_db,
    map_day_plans_to_response,
    select_related_place_docs,
    to_place_data_list,
)

router = APIRouter(prefix="/journeys", tags=["Journeys"])


@router.get(
    "",
    summary="List recent journeys",
    description="List recent journeys to quickly discover valid journey IDs"
)
async def list_journeys(limit: int = 20):
    """
    List recent journeys.

    Args:
        limit: Maximum number of journeys to return

    Returns:
        List of journey summaries
    """
    journey_repo = get_journey_repository()
    safe_limit = max(1, min(limit, 100))
    journeys = await journey_repo.list_recent(limit=safe_limit)

    results = []
    for journey in journeys:
        results.append({
            "_id": str(journey.get("_id")),
            "name": journey.get("name", "Unnamed Journey"),
            "owner_id": journey.get("owner_id"),
            "start_date": journey.get("start_date"),
            "end_date": journey.get("end_date"),
            "days_count": len(journey.get("days", [])),
            "updated_at": journey.get("updated_at"),
        })

    return {
        "journeys": results,
        "count": len(results),
    }


@router.post(
    "/auto-create-related",
    response_model=CreateJourneyFromRelatedResponse,
    summary="Create a new journey from related places",
    description="""
    Create a journey from related places and optionally auto-generate day plans.

    Related place selection strategy:
    - If `seed_place_id` is provided: prioritize nearby places and same-category places
    - Always merge with top approved places as fallback
    - Rank by rating, review count, category match, and tag overlap

    This endpoint does not require any database schema changes.
    """
)
async def create_journey_from_related_places(request: CreateJourneyFromRelatedRequest):
    """Create a new journey and optionally auto-plan it using related places."""
    if request.end_date < request.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be greater than or equal to start_date"
        )

    journey_repo = get_journey_repository()
    place_repo = get_place_repository()
    try:
        selected_docs = await select_related_place_docs(
            place_repo=place_repo,
            seed_place_id=request.seed_place_id,
            max_places=request.max_places,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    try:
        days, total_days = create_initial_days(
            start_date=request.start_date,
            end_date=request.end_date,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    now = datetime.utcnow()
    journey_doc = {
        "name": request.name,
        "owner_id": request.owner_id,
        "members": request.members,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "days": days,
        "total_budget": 0,
        "status": "DRAFT",
        "updated_at": now,
    }

    journey_id = await journey_repo.create_journey(journey_doc)
    if not journey_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create journey"
        )

    planning_notes: list[str] = []

    if request.auto_plan:
        places = to_place_data_list(selected_docs)

        planner = ItineraryPlanner(
            places=places,
            start_date=request.start_date,
            end_date=request.end_date,
            hours_per_day=request.hours_per_day,
            travel_style=request.travel_style,
            total_budget_vnd=request.total_budget_vnd,
            daily_budget_vnd=request.daily_budget_vnd,
            mode=request.mode,
            mood=request.mood,
            mood_distribution=None,
            start_location=None,
            max_places_per_day=5,
            must_include_categories=None,
            exclude_categories=None,
        )
        day_plans = planner.plan()

        db_days = map_day_plans_to_db(day_plans)
        await journey_repo.update_days(journey_id, db_days)
        planning_notes = planner.planning_notes

    return CreateJourneyFromRelatedResponse(
        journey_id=journey_id,
        journey_name=request.name,
        selected_places_count=len(selected_docs),
        selected_place_ids=[str(doc["_id"]) for doc in selected_docs],
        auto_planned=request.auto_plan,
        total_days=total_days,
        planning_notes=planning_notes,
    )


@router.post(
    "/{journey_id}/ai-plan",
    response_model=AIPlanResponse,
    summary="Generate AI-powered itinerary",
    description="""
    Generate an AI-powered itinerary for a journey.
    
    The AI will:
    - Analyze selected places
    - Calculate optimal routes using Haversine distance
    - Group nearby places into the same day
    - Optimize visit order within each day
    - Adjust durations based on travel style
    
    **Important**: The AI only uses places from the database.
    It does NOT hallucinate or invent new places.
    
    Travel styles:
    - **sightseeing**: More stops, shorter durations
    - **relaxing**: Fewer stops, longer durations  
    - **balanced**: Moderate pace
    """
)
async def generate_ai_plan(
    journey_id: str,
    request: AIPlanRequest
):
    """
    Generate AI itinerary for a journey.
    
    Args:
        journey_id: The journey's ObjectId
        request: Planning parameters (hours_per_day, travel_style, place_ids)
    
    Returns:
        AI-generated itinerary with reasoning for each stop
    """
    journey_repo = get_journey_repository()
    place_repo = get_place_repository()
    
    # Step 1: Fetch the journey
    journey = await journey_repo.get_by_id(journey_id)
    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journey with ID '{journey_id}' not found"
        )

    if request.mode == "group":
        requester = (request.requester_user_id or "").strip()
        owner = str(journey.get("owner_id", "")).strip()
        if requester and owner and requester != owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only journey owner can regenerate itinerary in group mode"
            )
    
    # Step 2: Get places for planning
    if request.place_ids and len(request.place_ids) > 0:
        # User specified specific places
        place_docs = await place_repo.get_by_ids(request.place_ids)
        if not place_docs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="None of the specified place IDs were found"
            )
    else:
        # Get existing places from journey days (if any stops exist)
        existing_place_ids = []
        for day in journey.get("days", []):
            for stop in day.get("stops", []):
                if "place_id" in stop:
                    existing_place_ids.append(stop["place_id"])
        
        if existing_place_ids:
            place_docs = await place_repo.get_by_ids(existing_place_ids)
        else:
            # No places specified - get top-rated places from database
            place_docs = await place_repo.get_all_approved(limit=20)
    
    if not place_docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No places available for planning. Add places to the journey first."
        )
    
    # Step 3: Convert to PlaceData for AI planning
    places = to_place_data_list(place_docs)
    
    # Step 4: Parse journey dates
    start_date = journey.get("start_date")
    end_date = journey.get("end_date")
    
    if not start_date or not end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Journey must have start_date and end_date"
        )
    
    # Ensure dates are datetime objects
    start_date = parse_iso_datetime(start_date)
    end_date = parse_iso_datetime(end_date)

    total_days = (end_date.date() - start_date.date()).days + 1
    if total_days < 1 or total_days > 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Journey total days must be between 1 and 4"
        )

    if request.total_days is not None and request.total_days != total_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request total_days={request.total_days} does not match journey range ({total_days})"
        )
    
    # Step 5: Run AI planning algorithm
    planner = ItineraryPlanner(
        places=places,
        start_date=start_date,
        end_date=end_date,
        hours_per_day=request.hours_per_day,
        travel_style=request.travel_style,
        total_budget_vnd=request.total_budget_vnd,
        daily_budget_vnd=request.daily_budget_vnd,
        mode=request.mode,
        mood=request.mood,
        mood_distribution=request.mood_distribution,
        start_location=request.start_location,
        max_places_per_day=request.max_places_per_day,
        must_include_categories=request.must_include_categories,
        exclude_categories=request.exclude_categories,
    )
    
    day_plans = planner.plan()
    
    # Step 6: Convert to response format
    response_days = map_day_plans_to_response(day_plans)
    
    # Step 7: Optionally update the journey in database
    db_days = map_day_plans_to_db(day_plans)
    
    await journey_repo.update_days(journey_id, db_days)

    planning_event = {
        "tripId": journey_id,
        "userId": request.requester_user_id or journey.get("owner_id"),
        "mode": request.mode,
        "mood": request.mood,
        "mood_distribution": planner.mood_distribution,
        "budgets": {
            "total_budget_vnd": request.total_budget_vnd,
            "daily_budget_vnd": request.daily_budget_vnd,
        },
        "candidate_pool_size": planner.candidate_pool_size,
        "selected_places": [
            {
                "day": day.get("day_number"),
                "place_id": stop.get("place_id"),
                "score": stop.get("final_score", 0.0),
            }
            for day in day_plans
            for stop in day.get("stops", [])
        ],
        "time_ms": planner.generation_time_ms,
    }
    print(f"[AI_PLANNING_EVENT] {planning_event}")
    
    return AIPlanResponse(
        journey_id=journey_id,
        journey_name=journey.get("name", "Unnamed Journey"),
        total_days=len(response_days),
        mode=request.mode,
        mood_used=request.mood,
        mood_distribution_used=planner.mood_distribution,
        total_budget_vnd=request.total_budget_vnd,
        daily_budget_vnd=request.daily_budget_vnd,
        generated_at=datetime.utcnow(),
        candidate_pool_size=planner.candidate_pool_size,
        generation_time_ms=planner.generation_time_ms,
        days=response_days,
        planning_notes=planner.planning_notes,
        algorithm_version="2.0.0",
    )


@router.get(
    "/{journey_id}/ai-explain",
    response_model=AIExplanation,
    summary="Get AI planning explanation",
    description="""
    Get a detailed explanation of how the AI planning algorithm works.
    
    This endpoint provides transparency into:
    - How distances are calculated
    - How places are grouped
    - How travel style affects the plan
    - What constraints are applied
    """
)
async def get_ai_explanation(journey_id: str):
    """
    Get explanation of AI planning algorithm.
    
    Args:
        journey_id: The journey's ObjectId
    
    Returns:
        Detailed explanation of planning logic
    """
    journey_repo = get_journey_repository()
    
    # Verify journey exists
    journey = await journey_repo.get_by_id(journey_id)
    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journey with ID '{journey_id}' not found"
        )
    
    # Return generic explanation (not journey-specific)
    # For journey-specific explanation, we'd need to store planning metadata
    return AIExplanation(
        journey_id=journey_id,
        algorithm_description=(
            "This itinerary was generated using a deterministic planning algorithm "
            "that considers geographic proximity, place ratings, travel style preferences, "
            "and time constraints. No machine learning or randomness is involved. "
            "The algorithm is fully reproducible given the same inputs."
        ),
        distance_calculation=(
            "Distances between places are calculated using the Haversine formula, "
            "which computes the great-circle distance between two points on Earth's surface. "
            "This accounts for the Earth's curvature and provides accurate distances "
            "for navigation purposes. Average travel speed is assumed to be 25 km/h, "
            "accounting for urban traffic, public transport, and walking."
        ),
        grouping_strategy=(
            "Places are grouped into daily clusters based on geographic proximity. "
            "The algorithm selects seed places that are geographically spread out "
            "(using a maximin strategy), then assigns remaining places to their nearest cluster. "
            "This ensures each day's itinerary covers a specific geographic area, "
            "minimizing travel time between stops."
        ),
        style_adjustments={
            "sightseeing": {
                "description": "Fast-paced exploration with more stops",
                "base_duration": "45 minutes per stop",
                "max_stops": 8,
                "buffer_time": "10 minutes between stops"
            },
            "relaxing": {
                "description": "Leisurely pace with fewer stops",
                "base_duration": "120 minutes per stop",
                "max_stops": 4,
                "buffer_time": "30 minutes between stops"
            },
            "balanced": {
                "description": "Moderate pace with balanced exploration",
                "base_duration": "75 minutes per stop",
                "max_stops": 6,
                "buffer_time": "20 minutes between stops"
            }
        },
        constraints_applied=[
            "Time constraint: Total daily activity must fit within specified hours",
            "Stop limit: Maximum number of stops based on travel style",
            "Travel time: Realistic travel times between consecutive stops",
            "Rating priority: Higher-rated places are preferred",
            "Geographic clustering: Nearby places grouped together"
        ],
        place_selection_criteria=[
            "Rating (40% weight): Places with higher ratings are prioritized",
            "Review count (20% weight): More reviews indicate reliability",
            "Category fit (40% weight): Attractions favored for sightseeing, restaurants for relaxing",
            "Geographic proximity: Places near each other scheduled on same day",
            "Time feasibility: Only places that fit within available time are included"
        ]
    )


@router.get(
    "/{journey_id}",
    summary="Get journey details",
    description="Get full journey details including all days and stops"
)
async def get_journey(journey_id: str):
    """
    Get journey by ID.
    
    Args:
        journey_id: The journey's ObjectId
    
    Returns:
        Journey document
    """
    journey_repo = get_journey_repository()
    
    journey = await journey_repo.get_by_id(journey_id)
    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journey with ID '{journey_id}' not found"
        )
    
    # Convert ObjectId to string for JSON serialization
    journey["_id"] = str(journey["_id"])
    
    return journey


@router.post(
    "/{journey_id}/days/{day_number}/stops/{place_id}",
    summary="Add a stop to a day",
    description="Manually add a place to a specific day in the journey"
)
async def add_stop_to_day(
    journey_id: str,
    day_number: int,
    place_id: str
):
    """
    Add a stop to a specific day.
    
    Args:
        journey_id: The journey's ObjectId
        day_number: Which day to add to
        place_id: The place to add
    
    Returns:
        Success message
    """
    journey_repo = get_journey_repository()
    place_repo = get_place_repository()
    
    # Verify journey exists
    journey = await journey_repo.get_by_id(journey_id)
    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journey with ID '{journey_id}' not found"
        )
    
    # Verify place exists
    place = await place_repo.get_by_id(place_id)
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Place with ID '{place_id}' not found"
        )
    
    # Get current stops count for order
    current_day = None
    for day in journey.get("days", []):
        if day.get("day_number") == day_number:
            current_day = day
            break
    
    if not current_day:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Day {day_number} not found in journey"
        )
    
    order = len(current_day.get("stops", [])) + 1
    coords = place.get("location", {}).get("coordinates", [0, 0])
    
    stop = {
        "place_id": place_id,
        "place_name": place.get("name", "Unknown"),
        "estimated_duration_minutes": 60,  # Default duration
        "reason": "Manually added by user",
        "order": order,
        "latitude": coords[1] if len(coords) > 1 else 0,
        "longitude": coords[0] if len(coords) > 0 else 0,
        "category": place.get("category", "ATTRACTION"),
    }
    
    success = await journey_repo.add_stop_to_day(journey_id, day_number, stop)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add stop"
        )
    
    return {"message": f"Added {place.get('name')} to day {day_number}"}


@router.delete(
    "/{journey_id}/days/{day_number}/stops/{place_id}",
    summary="Remove a stop from a day",
    description="Remove a place from a specific day in the journey"
)
async def remove_stop_from_day(
    journey_id: str,
    day_number: int,
    place_id: str
):
    """
    Remove a stop from a specific day.
    
    Args:
        journey_id: The journey's ObjectId
        day_number: Which day to remove from
        place_id: The place to remove
    
    Returns:
        Success message
    """
    journey_repo = get_journey_repository()
    
    success = await journey_repo.remove_stop_from_day(journey_id, day_number, place_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove stop"
        )
    
    return {"message": f"Removed stop from day {day_number}"}


@router.post(
    "/{journey_id}/days/{day_number}/improve-route-order",
    summary="Improve route order only",
    description="Reorder existing day stops to reduce distance without regenerating itinerary"
)
async def improve_route_order_only(journey_id: str, day_number: int):
    """Optimize stop order for one day and keep the same places."""
    journey_repo = get_journey_repository()
    journey = await journey_repo.get_by_id(journey_id)

    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journey with ID '{journey_id}' not found"
        )

    day_doc = next(
        (day for day in journey.get("days", []) if day.get("day_number") == day_number),
        None,
    )
    if not day_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Day {day_number} not found in journey"
        )

    raw_stops = day_doc.get("stops", [])
    if len(raw_stops) < 2:
        return {"message": "No optimization needed", "distance_before_km": 0.0, "distance_after_km": 0.0}

    place_like_stops: list[PlaceData] = []
    for stop in raw_stops:
        place_like_stops.append(
            PlaceData(
                id=stop.get("place_id"),
                name=stop.get("place_name", "Unknown"),
                latitude=float(stop.get("latitude", 0) or 0),
                longitude=float(stop.get("longitude", 0) or 0),
                category=stop.get("category", "ATTRACTION"),
                rating=4.0,
                review_count=0,
                tags=[],
                estimated_cost_vnd=int(stop.get("estimated_cost_vnd", 0) or 0),
                avg_visit_duration_min=int(stop.get("estimated_duration_minutes", 75) or 75),
                healing_score=3,
                crowd_level=3,
                image_url=None,
            )
        )

    distance_matrix = build_distance_matrix(place_like_stops)
    optimized = optimize_route_order(place_like_stops, distance_matrix)

    def route_distance(route: list[PlaceData]) -> float:
        total = 0.0
        for index in range(1, len(route)):
            total += distance_matrix[route[index - 1].id][route[index].id]
        return round(total, 2)

    before = route_distance(place_like_stops)
    after = route_distance(optimized)

    id_to_stop = {stop.get("place_id"): stop for stop in raw_stops}
    reordered_stops: list[dict] = []
    previous_place: PlaceData | None = None
    for order, place in enumerate(optimized, 1):
        stop_doc = dict(id_to_stop[place.id])
        stop_doc["order"] = order
        if previous_place:
            distance = distance_matrix[previous_place.id][place.id]
            stop_doc["distance_from_previous_km"] = round(distance, 2)
            stop_doc["travel_time_from_previous_minutes"] = estimate_travel_time(distance)
        else:
            stop_doc["distance_from_previous_km"] = 0.0
            stop_doc["travel_time_from_previous_minutes"] = 0
        reordered_stops.append(stop_doc)
        previous_place = place

    success = await journey_repo.reorder_stops(journey_id, day_number, reordered_stops)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reorder stops"
        )

    return {
        "message": f"Improved route order for day {day_number}",
        "distance_before_km": before,
        "distance_after_km": after,
        "optimized": after <= before,
    }
