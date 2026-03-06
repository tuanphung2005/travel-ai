"""
API Routes for Places endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional

from app.repositories import get_place_repository

router = APIRouter(prefix="/places", tags=["Places"])


@router.get(
    "",
    summary="Get all places",
    description="Get list of all approved places with optional filtering"
)
async def get_places(
    category: Optional[str] = Query(
        None, 
        description="Filter by category: ATTRACTION, HOTEL, RESTAURANT"
    ),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results")
):
    """
    Get list of places.
    
    Args:
        category: Optional category filter
        limit: Maximum number of results
    
    Returns:
        List of places
    """
    place_repo = get_place_repository()
    
    if category:
        places = await place_repo.get_by_category(category, limit)
    else:
        places = await place_repo.get_all_approved(limit)
    
    # Convert ObjectIds to strings
    for place in places:
        place["_id"] = str(place["_id"])
    
    return {"places": places, "count": len(places)}


@router.get(
    "/{place_id}",
    summary="Get place details",
    description="Get detailed information about a specific place"
)
async def get_place(place_id: str):
    """
    Get place by ID.
    
    Args:
        place_id: The place's ObjectId
    
    Returns:
        Place document
    """
    place_repo = get_place_repository()
    
    place = await place_repo.get_by_id(place_id)
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Place with ID '{place_id}' not found"
        )
    
    place["_id"] = str(place["_id"])
    return place


@router.get(
    "/nearby/search",
    summary="Find nearby places",
    description="Find places near a geographic point"
)
async def find_nearby_places(
    longitude: float = Query(..., description="Center point longitude"),
    latitude: float = Query(..., description="Center point latitude"),
    max_distance: int = Query(5000, ge=100, le=50000, description="Max distance in meters")
):
    """
    Find places near a geographic point.
    
    Args:
        longitude: Center longitude
        latitude: Center latitude
        max_distance: Maximum distance in meters
    
    Returns:
        List of nearby places
    """
    place_repo = get_place_repository()
    
    try:
        places = await place_repo.search_nearby(longitude, latitude, max_distance)
        
        for place in places:
            place["_id"] = str(place["_id"])
        
        return {"places": places, "count": len(places)}
    except Exception as e:
        # This might fail if 2dsphere index doesn't exist
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Geospatial query failed. Ensure 2dsphere index exists on location field. Error: {str(e)}"
        )


@router.post(
    "/enrich-scores",
    summary="Estimate and enrich missing healing/crowd scores",
    description="Uses rule-based heuristics to infer healing_score and crowd_level for places that lack them."
)
async def enrich_place_scores(
    dry_run: bool = Query(False, description="If true, returns what WOULD be enriched without modifying DB")
):
    """
    Find places missing healing_score/crowd_level and estimate them.
    
    Args:
        dry_run: preview changes without persisting
    
    Returns:
        Summary of enrichment operation
    """
    place_repo = get_place_repository()
    
    try:
        result = await place_repo.enrich_missing_scores(dry_run)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enrich scores. Error: {str(e)}"
        )
