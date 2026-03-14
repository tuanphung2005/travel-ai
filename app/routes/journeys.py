"""
API Routes for typical Journey CRUD operations.
"""
from fastapi import APIRouter, HTTPException, status, Query, Path
from app.repositories import (
    get_journey_repository,
    get_place_repository,
)

router = APIRouter(prefix="/journeys", tags=["Journeys"])


@router.get(
    "",
    summary="List recent journeys",
    response_description="Array of recent journeys with compact metadata",
    description="List recent journeys to quickly discover valid journey IDs"
)
async def list_journeys(limit: int = Query(20, ge=0, le=100)):
    """List recent journeys."""
    journey_repo = get_journey_repository()
    safe_limit = limit
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


@router.get(
    "/{journey_id}",
    summary="Get journey details",
    response_description="Full journey document including days and stops",
    description="Get full journey details including all days and stops",
    responses={
        404: {"description": "Journey not found"},
    },
)
async def get_journey(
    journey_id: str = Path(..., description="Journey ID (Mongo ObjectId as string)", examples=["67fd123abc9876543210f111"])
):
    """Get journey by ID."""
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


@router.delete(
    "/{journey_id}",
    summary="Delete a journey",
    response_description="Deletion confirmation",
    description="Delete a journey completely from the database",
    responses={
        404: {"description": "Journey not found"},
    },
)
async def delete_journey(
    journey_id: str = Path(..., description="Journey ID (Mongo ObjectId as string)", examples=["67fd123abc9876543210f111"])
):
    """Delete a journey by ID."""
    journey_repo = get_journey_repository()
    
    deleted = await journey_repo.delete_journey(journey_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journey with ID '{journey_id}' not found or could not be deleted"
        )
        
    return {"message": f"Successfully deleted journey {journey_id}"}


@router.post(
    "/{journey_id}/days/{day_number}/stops/{place_id}",
    summary="Add a stop to a day",
    response_description="Confirmation that stop was added",
    description="Manually add a place to a specific day in the journey",
    responses={
        400: {"description": "Day not found in journey"},
        404: {"description": "Journey or place not found"},
        500: {"description": "Failed to add stop"},
    },
)
async def add_stop_to_day(
    journey_id: str = Path(..., description="Journey ID (Mongo ObjectId as string)", examples=["67fd123abc9876543210f111"]),
    day_number: int = Path(..., ge=1, description="Day index in the journey", examples=[1]),
    place_id: str = Path(..., description="Place ID to add", examples=["67fd123abc9876543210f222"]),
):
    """Add a stop to a specific day."""
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
    response_description="Confirmation that stop was removed",
    description="Remove a place from a specific day in the journey",
    responses={
        500: {"description": "Failed to remove stop"},
    },
)
async def remove_stop_from_day(
    journey_id: str = Path(..., description="Journey ID (Mongo ObjectId as string)", examples=["67fd123abc9876543210f111"]),
    day_number: int = Path(..., ge=1, description="Day index in the journey", examples=[1]),
    place_id: str = Path(..., description="Place ID to remove", examples=["67fd123abc9876543210f222"]),
):
    """Remove a stop from a specific day."""
    journey_repo = get_journey_repository()
    
    success = await journey_repo.remove_stop_from_day(journey_id, day_number, place_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove stop"
        )
    
    return {"message": f"Removed stop from day {day_number}"}
