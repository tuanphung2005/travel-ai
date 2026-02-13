#!/bin/bash
# Test script for Travel Backend API

BASE_URL="http://localhost:8000/api/v1"
JOURNEY_ID="${1:-$JOURNEY_ID}"

fetch_latest_journey_id() {
  curl -s "$BASE_URL/journeys?limit=1" \
    | sed -n 's/.*"_id":"\([a-f0-9]\{24\}\)".*/\1/p' \
    | head -n1
}

echo "=== Testing Travel Backend API ==="
echo ""

# Test 1: Health Check
echo "1. Health Check"
curl -s http://localhost:8000/health
echo ""
echo ""

# Test 2: Get Places
echo "2. Get Places (first 5)"
curl -s "$BASE_URL/places?limit=5"
echo ""
echo ""

# Test 3: Get Journey
if [ -z "$JOURNEY_ID" ]; then
  JOURNEY_ID=$(fetch_latest_journey_id)

  if [ -z "$JOURNEY_ID" ]; then
    echo "3. Get Journey"
    echo "❌ Could not auto-fetch a journey ID."
    echo "   Ensure .env has MONGO_URI and DB_NAME, and journeys collection is not empty."
    echo "   You can still run: ./test_api.sh <journey_id>"
    echo ""
    exit 1
  fi

  echo "ℹ️  Auto-selected JOURNEY_ID: $JOURNEY_ID"
fi

echo "3. Get Journey"
JOURNEY_RESPONSE=$(curl -s "$BASE_URL/journeys/$JOURNEY_ID")
echo "$JOURNEY_RESPONSE"

if echo "$JOURNEY_RESPONSE" | grep -q '"detail":"Journey with ID'; then
  AUTO_JOURNEY_ID=$(fetch_latest_journey_id)

  if [ -n "$AUTO_JOURNEY_ID" ] && [ "$AUTO_JOURNEY_ID" != "$JOURNEY_ID" ]; then
    echo ""
    echo "⚠️  Journey ID not found: $JOURNEY_ID"
    echo "ℹ️  Retrying with auto-fetched JOURNEY_ID: $AUTO_JOURNEY_ID"
    JOURNEY_ID="$AUTO_JOURNEY_ID"
    JOURNEY_RESPONSE=$(curl -s "$BASE_URL/journeys/$JOURNEY_ID")
    echo "$JOURNEY_RESPONSE"
  fi

  if echo "$JOURNEY_RESPONSE" | grep -q '"detail":"Journey with ID'; then
    echo ""
    echo "❌ Journey not found in current database: $JOURNEY_ID"
    echo "   Check DB_NAME/MONGO_URI in .env and verify journeys collection has data."
    echo ""
    exit 1
  fi
fi

echo ""
echo ""

# Test 4: AI Plan Generation
echo "4. AI Plan Generation"
curl -s -X POST "$BASE_URL/journeys/$JOURNEY_ID/ai-plan" \
  -H "Content-Type: application/json" \
  -d '{
    "hours_per_day": 8,
    "travel_style": "balanced"
  }'
echo ""
echo ""

# Test 5: AI Explanation
echo "5. AI Explanation"
curl -s "$BASE_URL/journeys/$JOURNEY_ID/ai-explain"
echo ""
echo ""

echo "=== Tests Complete ==="
