# Travel Backend API

A FastAPI-based travel application with AI-assisted itinerary planning.

## Features

- 🗺️ Places listing and search
- 📍 Geospatial queries (nearby places)
- 🧳 Journey management
- 🤖 **AI-powered itinerary planning**

## Project Structure

```
travel-backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application entry point
│   ├── config.py         # Configuration management
│   ├── database.py       # MongoDB connection
│   ├── models.py         # Pydantic models
│   ├── ai_planner.py     # AI planning algorithm
│   ├── repositories.py   # Database operations
│   └── routes/
│       ├── __init__.py
│       ├── journeys.py   # Journey & AI planning endpoints
│       └── places.py     # Places endpoints
├── .env                  # Environment variables
├── requirements.txt      # Python dependencies
├── run.sh               # Run script
└── README.md
```

## Setup

### 1. Create virtual environment

```bash
cd /mnt/c/Users/tuan2/coding/travel-backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Create `.env` file with:

```
MONGO_URI=mongodb+srv://...
DB_NAME=berotravel
```

### 4. Run the application

```bash
# Option 1: Using run script
./run.sh

# Option 2: Direct uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Access the API

- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

### 6. Run API smoke test script

`test_api.sh` requires a real journey ID from your current database.

```bash
./test_api.sh <journey_id>
# or
JOURNEY_ID=<journey_id> ./test_api.sh
```

## API Endpoints

### Places

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/places` | List all places |
| GET | `/api/v1/places/{id}` | Get place details |
| GET | `/api/v1/places/nearby/search` | Find nearby places |

### Journeys

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/journeys/{id}` | Get journey details |
| POST | `/api/v1/journeys/{id}/ai-plan` | Generate AI itinerary |
| GET | `/api/v1/journeys/{id}/ai-explain` | Get AI explanation |
| POST | `/api/v1/journeys/{id}/days/{day}/stops/{place_id}` | Add stop manually |
| DELETE | `/api/v1/journeys/{id}/days/{day}/stops/{place_id}` | Remove stop |

## AI Planning System

### How It Works

The AI planning system is **deterministic and explainable**:

1. **Distance Calculation**: Uses Haversine formula for accurate geographic distances
2. **Geographic Clustering**: Groups nearby places into same-day itineraries
3. **Route Optimization**: Uses nearest neighbor algorithm to minimize travel time
4. **Style Adaptation**: Adjusts durations and stop counts based on travel style

### Travel Styles

| Style | Stops/Day | Duration/Stop | Description |
|-------|-----------|---------------|-------------|
| sightseeing | 4-8 | 45 min | Fast-paced exploration |
| relaxing | 2-4 | 120 min | Leisurely enjoyment |
| balanced | 3-6 | 75 min | Moderate pace |

### AI Request Example

```json
POST /api/v1/journeys/{journey_id}/ai-plan
{
    "hours_per_day": 8,
    "travel_style": "balanced",
    "place_ids": ["6953524453ece5575927223a", "..."]
}
```

### AI Response Example

```json
{
    "journey_id": "6965ac017591cb43d71ed462",
    "journey_name": "Hành trình khám phá Phú Thọ",
    "total_days": 3,
    "travel_style": "balanced",
    "hours_per_day": 8,
    "days": [
        {
            "day_number": 1,
            "date": "2026-01-15T00:00:00",
            "stops": [
                {
                    "place_id": "6953524453ece5575927223a",
                    "place_name": "Hoàng Thành Thăng Long",
                    "estimated_duration_minutes": 90,
                    "reason": "Highly rated (4.4★). Popular attraction. fits balanced exploration.",
                    "order": 1,
                    "travel_time_from_previous_minutes": 0,
                    "distance_from_previous_km": 0,
                    "latitude": 21.0352231,
                    "longitude": 105.8402594,
                    "category": "ATTRACTION",
                    "rating": 4.4
                }
            ],
            "total_duration_minutes": 90,
            "total_travel_time_minutes": 0,
            "summary": "Day 1: 1 stops, 90 mins visiting, 0 mins traveling."
        }
    ],
    "planning_notes": [
        "Planning 1 places over 3 days with 8 hours/day in 'balanced' style.",
        "Top rated place: Hoàng Thành Thăng Long (score: 76.26)",
        "Created 1 geographic clusters for 3 days.",
        "Planning complete. Total stops: 1"
    ],
    "algorithm_version": "1.0.0"
}
```

## Important Rules

- ✅ AI only uses places from database
- ✅ All decisions are explainable
- ✅ Algorithm is deterministic and reproducible
- ❌ AI does NOT hallucinate places
- ❌ AI does NOT make random decisions

## Database Schema

### places collection

```javascript
{
  _id: ObjectId,
  google_id: string,
  name: string,
  description: string,
  category: "ATTRACTION" | "HOTEL" | "RESTAURANT",
  address: string,
  location: {
    type: "Point",
    coordinates: [longitude, latitude]
  },
  rating: number,
  reviewCount: number,
  priceLevel: number,
  tags: string[],
  status: "APPROVED" | "PENDING"
}
```

### journeys collection

```javascript
{
  _id: ObjectId,
  name: string,
  owner_id: string,
  members: string[],
  start_date: Date,
  end_date: Date,
  days: [
    {
      day_number: number,
      date: Date,
      stops: [
        {
          place_id: string,
          place_name: string,
          estimated_duration_minutes: number,
          reason: string,
          order: number
        }
      ]
    }
  ]
}
```

## MongoDB Index Recommendations

```javascript
// For geospatial queries
db.places.createIndex({ location: "2dsphere" })

// For journey lookups
db.journeys.createIndex({ owner_id: 1 })
db.journeys.createIndex({ "days.day_number": 1 })
```

## Algorithm Details

### Haversine Formula

```
a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
c = 2 * atan2(√a, √(1-a))
d = R * c

Where R = 6371 km (Earth's radius)
```

### Place Scoring

```
Score = Rating_Score (40%) + Review_Score (20%) + Category_Score (40%)

Rating_Score = (rating / 5.0) * 40
Review_Score = min(20, log10(reviewCount) * 5)
Category_Score = Based on travel style preference
```

## License

MIT License - For University Software Engineering Project
