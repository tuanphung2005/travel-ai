#!/bin/bash
# Test script for Travel Backend API

BASE_URL="http://localhost:8000/api/v1"

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

# Test 3: Get Journey (use your actual journey ID)
JOURNEY_ID="6965ac017591cb43d71ed462"
echo "3. Get Journey"
curl -s "$BASE_URL/journeys/$JOURNEY_ID"
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
