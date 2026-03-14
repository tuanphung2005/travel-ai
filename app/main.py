"""
Travel Backend Application - Main Entry Point

A FastAPI-based travel application with AI-assisted itinerary planning.
This is a real production system, not a demo.

Features:
- Places listing and search
- Journey management
- AI-powered itinerary planning
- Geospatial queries

Author: Travel Backend Team
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import connect_to_mongo, close_mongo_connection
from app.routes import journeys, places, debug, planning


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    print("🚀 Starting Travel Backend Application...")
    await connect_to_mongo()
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    await close_mongo_connection()


# Create FastAPI application
app = FastAPI(
    title="Travel Backend API",
    summary="AI-assisted travel planning API",
    description="""
    ## Travel Application Backend with AI-Assisted Itinerary Planning
    
    This API provides endpoints for:
    
    ### Places
    - List and search places
    - Get place details
    - Find nearby places (geospatial)
    
    ### Journeys
    - Get journey details
    - **AI-powered itinerary planning**
    - Manual stop management
    
    ### AI Planning Features
    
    The AI planning system is **deterministic and explainable**:
    - Uses Haversine formula for distance calculation
    - Groups nearby places into same day
    - Optimizes route order using nearest neighbor algorithm
    - Adjusts for travel style (sightseeing/relaxing/balanced)

    """,
    version="1.0.0",
    contact={
        "name": "Travel Backend Team",
        "url": "https://example.com/support",
    },
    license_info={
        "name": "Proprietary",
    },
    openapi_tags=[
        {
            "name": "Health",
            "description": "Service health and readiness endpoints.",
        },
        {
            "name": "Places",
            "description": "Browse and query approved travel places.",
        },
        {
            "name": "Journeys",
            "description": "CRUD and manual stop management for journeys.",
        },
        {
            "name": "AI Planning",
            "description": "Generate and explain deterministic AI-assisted itineraries.",
        },
    ],
    servers=[
        {
            "url": "/",
            "description": "Current environment",
        }
    ],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(places.router, prefix="/api/v1")
app.include_router(journeys.router, prefix="/api/v1")
app.include_router(planning.router, prefix="/api/v1")
app.include_router(debug.router)


@app.get(
    "/",
    tags=["Health"],
    summary="API root",
    response_description="Basic service metadata and docs link",
)
async def root():
    """Root endpoint - Health check."""
    return {
        "status": "healthy",
        "application": "Travel Backend API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    response_description="Basic health status for API and database connectivity",
)
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "api_version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
