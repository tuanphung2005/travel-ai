You are a senior backend + AI engineer.

I am building a real travel application with AI-assisted itinerary planning.
This is NOT a demo or fake AI.
I already have MongoDB Atlas connected and real data.

Your task is to design and implement the AI journey planning logic, backend flow, and data handling.

You must follow everything below strictly.

---

## 1. APPLICATION FLOW OVERVIEW

### App type

Travel app with:

* places listing
* reviews
* journeys (travel itineraries)
* AI-assisted itinerary planning

AI does NOT make final decisions.
AI only suggests.
User can edit everything.

---

## 2. USER FLOW

### 1. Open app

* If not logged in → register / login
* If logged in → home page

### 2. Home page (NO AI)

* show weather
* show list of places
* view place detail
* navigation to:

  * Journey
  * Booking
  * Notification
  * Account

### 3. Place detail (NO AI)

* show place info
* show reviews
* add place to journey
* book hotel (mock payment)

### 4. Journey (AI INCLUDED)

User sees:

* journey info
* selected places
* travel dates

User can choose:

* "Auto plan with AI"
* "Manual arrangement"

---

## 4.1 AI Auto Planning

User inputs:

* number_of_days
* available_hours_per_day
* travel_style:

  * sightseeing
  * relaxing
  * balanced

AI must consider:

* geographic distance between places (latitude/longitude)
* estimated travel time
* rating
* weather (mocked)
* user travel style
* avoid overcrowding daily schedule

AI output:

* structured itinerary
* separated by day
* ordered stops per day
* estimated visit duration
* reasoning for each suggestion

AI must NOT hallucinate places.
AI can ONLY use places from database.

---

## 4.2 Review & Edit

After AI generates itinerary:

* user can reorder stops
* delete stops
* add new places manually

AI suggestions are non-destructive.

---

## 5. DATABASE STRUCTURE (ALREADY EXISTS)

### Collections:

* users
* places
* journeys
* availability
* chat_messages
* groups

---

### places schema example

```
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
  tags: string[]
}
```

---

### journeys schema example

```
{
  _id: ObjectId,
  name: string,
  owner_id: string,
  start_date: Date,
  end_date: Date,
  days: [
    {
      day_number: number,
      date: Date,
      stops: []
    }
  ]
}
```

---

## 6. AI SYSTEM REQUIREMENTS

You must implement AI as a deterministic decision-support system.

### AI responsibilities:

1. Read journey date range
2. Fetch selected places
3. Compute distance between places using coordinates
4. Group nearby places into same day
5. Limit number of stops per day based on available hours
6. Adjust based on travel style:

   * sightseeing → more stops, shorter duration
   * relaxing → fewer stops, longer duration
   * balanced → moderate

---

### AI must output:

```
{
  day_number: 1,
  stops: [
    {
      place_id,
      place_name,
      estimated_duration_minutes,
      reason
    }
  ]
}
```

---

## 7. TECHNICAL REQUIREMENTS

* Backend: FastAPI
* MongoDB Atlas
* No deep learning required
* Use geographic distance calculation (Haversine formula)
* All AI logic must be explainable
* No black-box behavior

---

## 8. API ENDPOINTS TO IMPLEMENT

### Generate itinerary

```
POST /journeys/{journey_id}/ai-plan
```

Request body:

```
{
  "hours_per_day": 8,
  "travel_style": "balanced"
}
```

Response:

* updated journey with AI suggested stops

---

### Optional AI explanation endpoint

```
GET /journeys/{journey_id}/ai-explain
```

Returns:

* explanation of how itinerary was generated

---

## 9. IMPORTANT RULES

* DO NOT invent new places
* DO NOT use random outputs
* DO NOT hallucinate
* ONLY use database data
* AI must be reproducible

---

## 10. OUTPUT EXPECTATION

You must generate:

1. Clean backend architecture
2. AI planning algorithm
3. Distance calculation logic
4. Example Mongo queries
5. Clear comments explaining AI logic
6. Production-readable code

This system is for a university Software Engineering project but must reflect real-world engineering practices.

Focus on correctness, clarity, and maintainability.

---

Start by designing the AI planning algorithm first, then implement the backend endpoint.

Do NOT skip reasoning explanation.
