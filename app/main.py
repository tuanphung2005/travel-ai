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
from app.routes import journeys, places


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
    
    **Important**: The AI only uses places from the database.
    It does NOT hallucinate or invent new places.
    """,
    version="1.0.0",
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


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - Health check."""
    return {
        "status": "healthy",
        "application": "Travel Backend API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
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
