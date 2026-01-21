"""
API Routes for Journey and AI Planning endpoints.
"""
from fastapi import APIRouter, HTTPException, status
from datetime import datetime

from app.models import (
    AIPlanRequest,
    AIPlanResponse,
    AIDayPlan,
    AIStopSuggestion,
    AIExplanation,
)
from app.repositories import (
    get_journey_repository,
    get_place_repository,
    PlaceRepository,
)
from app.ai_planner import ItineraryPlanner, PlaceData

router = APIRouter(prefix="/journeys", tags=["Journeys"])


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
    places: list[PlaceData] = [
        PlaceRepository.to_place_data(doc) 
        for doc in place_docs
    ]
    
    # Step 4: Parse journey dates
    start_date = journey.get("start_date")
    end_date = journey.get("end_date")
    
    if not start_date or not end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Journey must have start_date and end_date"
        )
    
    # Ensure dates are datetime objects
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    if isinstance(end_date, str):
        end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    
    # Step 5: Run AI planning algorithm
    planner = ItineraryPlanner(
        places=places,
        start_date=start_date,
        end_date=end_date,
        hours_per_day=request.hours_per_day,
        travel_style=request.travel_style
    )
    
    day_plans = planner.plan()
    
    # Step 6: Convert to response format
    response_days = []
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
    
    # Step 7: Optionally update the journey in database
    # Convert day_plans to the format expected by MongoDB
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
    
    await journey_repo.update_days(journey_id, db_days)
    
    return AIPlanResponse(
        journey_id=journey_id,
        journey_name=journey.get("name", "Unnamed Journey"),
        total_days=len(response_days),
        travel_style=request.travel_style,
        hours_per_day=request.hours_per_day,
        days=response_days,
        planning_notes=planner.planning_notes,
        algorithm_version="1.0.0",
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
