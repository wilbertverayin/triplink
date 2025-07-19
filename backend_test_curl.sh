#!/bin/bash

# TripLink Backend API Test Script using curl
# Tests all backend functionality including authentication, trips, bookings, and provider features.

BASE_URL="https://099871a3-8a0b-4278-bde3-7cd102dc1ac9.preview.emergentagent.com/api"

echo "🚀 TESTING TRIPLINK BACKEND API WITH CURL"
echo "Base URL: $BASE_URL"
echo "============================================================"

# Global variables
PASSENGER_TOKEN=""
PROVIDER_TOKEN=""
TRIP_ID=""
BOOKING_ID=""

echo ""
echo "🔐 TESTING AUTHENTICATION SYSTEM"
echo "----------------------------------------"

# Test 1: Register passenger
echo "1. Testing passenger registration..."
PASSENGER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Maria Santos",
    "email": "maria.santos.test@email.com",
    "password": "securepass123",
    "role": "passenger",
    "phone": "+639171234567"
  }' --max-time 10)

if echo "$PASSENGER_RESPONSE" | grep -q '"token"'; then
    PASSENGER_TOKEN=$(echo "$PASSENGER_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Passenger registered successfully"
    echo "   Token: ${PASSENGER_TOKEN:0:20}..."
else
    echo "❌ Passenger registration failed"
    echo "   Response: $PASSENGER_RESPONSE"
fi

# Test 2: Register provider
echo ""
echo "2. Testing provider registration..."
PROVIDER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Juan Transport Co.",
    "email": "juan.transport.test@email.com",
    "password": "providerpass123",
    "role": "provider",
    "phone": "+639181234567"
  }' --max-time 10)

if echo "$PROVIDER_RESPONSE" | grep -q '"token"'; then
    PROVIDER_TOKEN=$(echo "$PROVIDER_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Provider registered successfully"
    echo "   Token: ${PROVIDER_TOKEN:0:20}..."
else
    echo "❌ Provider registration failed"
    echo "   Response: $PROVIDER_RESPONSE"
fi

# Test 3: Login test
echo ""
echo "3. Testing passenger login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "maria.santos.test@email.com",
    "password": "securepass123"
  }' --max-time 10)

if echo "$LOGIN_RESPONSE" | grep -q '"role":"passenger"'; then
    echo "✅ Passenger login successful"
else
    echo "❌ Passenger login failed"
    echo "   Response: $LOGIN_RESPONSE"
fi

# Test 4: Invalid login
echo ""
echo "4. Testing invalid login..."
INVALID_LOGIN_RESPONSE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "maria.santos.test@email.com",
    "password": "wrongpassword"
  }' --max-time 10)

if echo "$INVALID_LOGIN_RESPONSE" | grep -q "401"; then
    echo "✅ Invalid login correctly rejected"
else
    echo "❌ Invalid login handling failed"
    echo "   Response: $INVALID_LOGIN_RESPONSE"
fi

echo ""
echo "🚌 TESTING TRIP MANAGEMENT"
echo "----------------------------------------"

# Test 5: Create trip as provider
echo "1. Testing trip creation (as provider)..."
if [ -n "$PROVIDER_TOKEN" ]; then
    TOMORROW=$(date -d "+1 day" -Iseconds)
    TRIP_RESPONSE=$(curl -s -X POST "$BASE_URL/trips" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $PROVIDER_TOKEN" \
      -d "{
        \"origin\": \"Manila\",
        \"destination\": \"Baguio\",
        \"departure_time\": \"$TOMORROW\",
        \"vehicle_type\": \"bus\",
        \"price_per_seat\": 850.0,
        \"seat_capacity\": 45,
        \"amenities\": [\"WiFi\", \"AC\", \"Restroom\"],
        \"vehicle_name\": \"Victory Liner Express\"
      }" --max-time 10)
    
    if echo "$TRIP_RESPONSE" | grep -q '"id"'; then
        TRIP_ID=$(echo "$TRIP_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
        echo "✅ Trip created successfully: Manila → Baguio"
        echo "   Trip ID: $TRIP_ID"
    else
        echo "❌ Trip creation failed"
        echo "   Response: $TRIP_RESPONSE"
    fi
else
    echo "❌ No provider token available"
fi

# Test 6: Unauthorized trip creation (as passenger)
echo ""
echo "2. Testing unauthorized trip creation (as passenger)..."
if [ -n "$PASSENGER_TOKEN" ]; then
    UNAUTH_TRIP_RESPONSE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/trips" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $PASSENGER_TOKEN" \
      -d "{
        \"origin\": \"Manila\",
        \"destination\": \"Baguio\",
        \"departure_time\": \"$TOMORROW\",
        \"vehicle_type\": \"bus\",
        \"price_per_seat\": 850.0,
        \"seat_capacity\": 45,
        \"amenities\": [\"WiFi\", \"AC\", \"Restroom\"],
        \"vehicle_name\": \"Victory Liner Express\"
      }" --max-time 10)
    
    if echo "$UNAUTH_TRIP_RESPONSE" | grep -q "403"; then
        echo "✅ Passenger correctly denied trip creation"
    else
        echo "❌ Authorization check failed"
        echo "   Response: $UNAUTH_TRIP_RESPONSE"
    fi
else
    echo "❌ No passenger token available"
fi

# Test 7: Search trips
echo ""
echo "3. Testing trip search..."
SEARCH_RESPONSE=$(curl -s -X GET "$BASE_URL/trips/search" \
  -H "Content-Type: application/json" --max-time 10)

if echo "$SEARCH_RESPONSE" | grep -q '"origin"'; then
    TRIP_COUNT=$(echo "$SEARCH_RESPONSE" | grep -o '"id"' | wc -l)
    echo "✅ Trip search successful: Found $TRIP_COUNT trips"
else
    echo "❌ Trip search failed"
    echo "   Response: $SEARCH_RESPONSE"
fi

# Test 8: Search trips with filters
echo ""
echo "4. Testing trip search with filters..."
FILTERED_SEARCH_RESPONSE=$(curl -s -X GET "$BASE_URL/trips/search?origin=Manila&destination=Baguio&vehicle_type=bus" \
  -H "Content-Type: application/json" --max-time 10)

if echo "$FILTERED_SEARCH_RESPONSE" | grep -q '"origin"'; then
    FILTERED_TRIP_COUNT=$(echo "$FILTERED_SEARCH_RESPONSE" | grep -o '"id"' | wc -l)
    echo "✅ Filtered trip search successful: Found $FILTERED_TRIP_COUNT trips"
else
    echo "❌ Filtered trip search failed"
    echo "   Response: $FILTERED_SEARCH_RESPONSE"
fi

echo ""
echo "🎫 TESTING BOOKING SYSTEM"
echo "----------------------------------------"

# Test 9: Get seat availability
echo "1. Testing seat availability..."
if [ -n "$TRIP_ID" ]; then
    SEATS_RESPONSE=$(curl -s -X GET "$BASE_URL/trips/$TRIP_ID/seats" \
      -H "Content-Type: application/json" --max-time 10)
    
    if echo "$SEATS_RESPONSE" | grep -q '"seats"'; then
        echo "✅ Seat availability retrieved successfully"
        # Find first available seat (assuming seat 1 is available)
        SEAT_NUMBER=1
        echo "   Will book seat number: $SEAT_NUMBER"
    else
        echo "❌ Get seat availability failed"
        echo "   Response: $SEATS_RESPONSE"
    fi
else
    echo "❌ No trip ID available for seat check"
fi

# Test 10: Create booking as passenger
echo ""
echo "2. Testing booking creation (as passenger)..."
if [ -n "$PASSENGER_TOKEN" ] && [ -n "$TRIP_ID" ]; then
    BOOKING_RESPONSE=$(curl -s -X POST "$BASE_URL/bookings" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $PASSENGER_TOKEN" \
      -d "{
        \"trip_id\": \"$TRIP_ID\",
        \"seat_number\": $SEAT_NUMBER
      }" --max-time 10)
    
    if echo "$BOOKING_RESPONSE" | grep -q '"id"'; then
        BOOKING_ID=$(echo "$BOOKING_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
        echo "✅ Booking created successfully: Seat $SEAT_NUMBER"
        echo "   Booking ID: $BOOKING_ID"
        
        # Check if QR code is generated
        if echo "$BOOKING_RESPONSE" | grep -q '"qr_code":"data:image/png;base64,'; then
            echo "   QR Code generated: ✅"
        else
            echo "   QR Code generated: ❌"
        fi
    else
        echo "❌ Booking creation failed"
        echo "   Response: $BOOKING_RESPONSE"
    fi
else
    echo "❌ Missing passenger token or trip ID"
fi

# Test 11: Test duplicate booking
echo ""
echo "3. Testing duplicate booking (should fail)..."
if [ -n "$PASSENGER_TOKEN" ] && [ -n "$TRIP_ID" ]; then
    DUPLICATE_BOOKING_RESPONSE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/bookings" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $PASSENGER_TOKEN" \
      -d "{
        \"trip_id\": \"$TRIP_ID\",
        \"seat_number\": $SEAT_NUMBER
      }" --max-time 10)
    
    if echo "$DUPLICATE_BOOKING_RESPONSE" | grep -q "400"; then
        echo "✅ Duplicate booking correctly rejected"
    else
        echo "❌ Duplicate booking handling failed"
        echo "   Response: $DUPLICATE_BOOKING_RESPONSE"
    fi
fi

# Test 12: Get passenger bookings
echo ""
echo "4. Testing get passenger bookings..."
if [ -n "$PASSENGER_TOKEN" ]; then
    MY_BOOKINGS_RESPONSE=$(curl -s -X GET "$BASE_URL/bookings/my" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $PASSENGER_TOKEN" --max-time 10)
    
    if echo "$MY_BOOKINGS_RESPONSE" | grep -q '"booking"'; then
        BOOKING_COUNT=$(echo "$MY_BOOKINGS_RESPONSE" | grep -o '"booking"' | wc -l)
        echo "✅ Passenger bookings retrieved: $BOOKING_COUNT bookings"
    else
        echo "❌ Get passenger bookings failed"
        echo "   Response: $MY_BOOKINGS_RESPONSE"
    fi
fi

echo ""
echo "👨‍💼 TESTING PROVIDER FEATURES"
echo "----------------------------------------"

# Test 13: Get provider bookings dashboard
echo "1. Testing provider bookings dashboard..."
if [ -n "$PROVIDER_TOKEN" ]; then
    PROVIDER_BOOKINGS_RESPONSE=$(curl -s -X GET "$BASE_URL/provider/bookings" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $PROVIDER_TOKEN" --max-time 10)
    
    if echo "$PROVIDER_BOOKINGS_RESPONSE" | grep -q '"booking"'; then
        PROVIDER_BOOKING_COUNT=$(echo "$PROVIDER_BOOKINGS_RESPONSE" | grep -o '"booking"' | wc -l)
        echo "✅ Provider bookings dashboard retrieved: $PROVIDER_BOOKING_COUNT bookings"
    else
        echo "❌ Get provider bookings failed"
        echo "   Response: $PROVIDER_BOOKINGS_RESPONSE"
    fi
fi

# Test 14: Check-in passenger
echo ""
echo "2. Testing passenger check-in..."
if [ -n "$PROVIDER_TOKEN" ] && [ -n "$BOOKING_ID" ]; then
    CHECKIN_RESPONSE=$(curl -s -w "%{http_code}" -X PUT "$BASE_URL/provider/bookings/$BOOKING_ID/checkin" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $PROVIDER_TOKEN" --max-time 10)
    
    if echo "$CHECKIN_RESPONSE" | grep -q "200"; then
        echo "✅ Passenger check-in successful"
    else
        echo "❌ Passenger check-in failed"
        echo "   Response: $CHECKIN_RESPONSE"
    fi
fi

echo ""
echo "⚠️  TESTING ERROR HANDLING"
echo "----------------------------------------"

# Test 15: Invalid token
echo "1. Testing invalid token..."
INVALID_TOKEN_RESPONSE=$(curl -s -w "%{http_code}" -X GET "$BASE_URL/trips/my" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer invalid_token_here" --max-time 10)

if echo "$INVALID_TOKEN_RESPONSE" | grep -q "401"; then
    echo "✅ Invalid token correctly rejected"
else
    echo "❌ Invalid token handling failed"
    echo "   Response: $INVALID_TOKEN_RESPONSE"
fi

# Test 16: Missing token
echo ""
echo "2. Testing missing token..."
MISSING_TOKEN_RESPONSE=$(curl -s -w "%{http_code}" -X GET "$BASE_URL/trips/my" \
  -H "Content-Type: application/json" --max-time 10)

if echo "$MISSING_TOKEN_RESPONSE" | grep -q "403"; then
    echo "✅ Missing token correctly rejected"
else
    echo "❌ Missing token handling failed"
    echo "   Response: $MISSING_TOKEN_RESPONSE"
fi

# Test 17: Duplicate email registration
echo ""
echo "3. Testing duplicate email registration..."
DUPLICATE_EMAIL_RESPONSE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Another Maria",
    "email": "maria.santos.test@email.com",
    "password": "anotherpass123",
    "role": "passenger"
  }' --max-time 10)

if echo "$DUPLICATE_EMAIL_RESPONSE" | grep -q "400"; then
    echo "✅ Duplicate email registration correctly rejected"
else
    echo "❌ Duplicate email handling failed"
    echo "   Response: $DUPLICATE_EMAIL_RESPONSE"
fi

echo ""
echo "============================================================"
echo "🎉 ALL CURL TESTS COMPLETED"
echo "============================================================"