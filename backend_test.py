#!/usr/bin/env python3
"""
TripLink Backend API Testing Suite
Tests all backend functionality including authentication, trips, bookings, and provider features.
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get base URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL')
if not BACKEND_URL:
    raise ValueError("REACT_APP_BACKEND_URL not found in environment")

BASE_URL = f"{BACKEND_URL}/api"

print(f"Testing TripLink API at: {BASE_URL}")
print("=" * 60)

# Global variables to store tokens and IDs
passenger_token = None
provider_token = None
passenger_user = None
provider_user = None
test_trip_id = None
test_booking_id = None

def make_request(method, endpoint, data=None, headers=None, params=None):
    """Helper function to make HTTP requests"""
    url = f"{BASE_URL}{endpoint}"
    
    default_headers = {"Content-Type": "application/json"}
    if headers:
        default_headers.update(headers)
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=default_headers, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, headers=default_headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=default_headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=default_headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        return response
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_authentication():
    """Test user registration and login for both passenger and provider"""
    global passenger_token, provider_token, passenger_user, provider_user
    
    print("\n🔐 TESTING AUTHENTICATION SYSTEM")
    print("-" * 40)
    
    # Test passenger registration
    print("1. Testing passenger registration...")
    passenger_data = {
        "name": "Maria Santos",
        "email": "maria.santos@email.com",
        "password": "securepass123",
        "role": "passenger",
        "phone": "+639171234567"
    }
    
    response = make_request("POST", "/auth/register", passenger_data)
    if response and response.status_code == 200:
        result = response.json()
        passenger_token = result["token"]
        passenger_user = result["user"]
        print(f"✅ Passenger registered successfully: {passenger_user['name']}")
        print(f"   Token received: {passenger_token[:20]}...")
    else:
        print(f"❌ Passenger registration failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"   Error: {response.text}")
    
    # Test provider registration
    print("\n2. Testing provider registration...")
    provider_data = {
        "name": "Juan Transport Co.",
        "email": "juan.transport@email.com", 
        "password": "providerpass123",
        "role": "provider",
        "phone": "+639181234567"
    }
    
    response = make_request("POST", "/auth/register", provider_data)
    if response and response.status_code == 200:
        result = response.json()
        provider_token = result["token"]
        provider_user = result["user"]
        print(f"✅ Provider registered successfully: {provider_user['name']}")
        print(f"   Token received: {provider_token[:20]}...")
    else:
        print(f"❌ Provider registration failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"   Error: {response.text}")
    
    # Test login with passenger
    print("\n3. Testing passenger login...")
    login_data = {
        "email": "maria.santos@email.com",
        "password": "securepass123"
    }
    
    response = make_request("POST", "/auth/login", login_data)
    if response and response.status_code == 200:
        result = response.json()
        print(f"✅ Passenger login successful")
        print(f"   User role: {result['user']['role']}")
    else:
        print(f"❌ Passenger login failed: {response.status_code if response else 'No response'}")
    
    # Test invalid login
    print("\n4. Testing invalid login...")
    invalid_login = {
        "email": "maria.santos@email.com",
        "password": "wrongpassword"
    }
    
    response = make_request("POST", "/auth/login", invalid_login)
    if response and response.status_code == 401:
        print("✅ Invalid login correctly rejected")
    else:
        print(f"❌ Invalid login handling failed: {response.status_code if response else 'No response'}")

def test_trip_management():
    """Test trip creation, search, and management"""
    global test_trip_id
    
    print("\n🚌 TESTING TRIP MANAGEMENT")
    print("-" * 40)
    
    # Test trip creation as provider
    print("1. Testing trip creation (as provider)...")
    if not provider_token:
        print("❌ No provider token available")
        return
    
    # Create a trip for tomorrow
    tomorrow = datetime.now() + timedelta(days=1)
    trip_data = {
        "origin": "Manila",
        "destination": "Baguio",
        "departure_time": tomorrow.isoformat(),
        "vehicle_type": "bus",
        "price_per_seat": 850.0,
        "seat_capacity": 45,
        "amenities": ["WiFi", "AC", "Restroom"],
        "vehicle_name": "Victory Liner Express"
    }
    
    headers = {"Authorization": f"Bearer {provider_token}"}
    response = make_request("POST", "/trips", trip_data, headers)
    
    if response and response.status_code == 200:
        result = response.json()
        test_trip_id = result["id"]
        print(f"✅ Trip created successfully: {result['origin']} → {result['destination']}")
        print(f"   Trip ID: {test_trip_id}")
        print(f"   Available seats: {result['available_seats']}")
    else:
        print(f"❌ Trip creation failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"   Error: {response.text}")
    
    # Test unauthorized trip creation (as passenger)
    print("\n2. Testing unauthorized trip creation (as passenger)...")
    headers = {"Authorization": f"Bearer {passenger_token}"}
    response = make_request("POST", "/trips", trip_data, headers)
    
    if response and response.status_code == 403:
        print("✅ Passenger correctly denied trip creation")
    else:
        print(f"❌ Authorization check failed: {response.status_code if response else 'No response'}")
    
    # Test trip search without filters
    print("\n3. Testing trip search (no filters)...")
    response = make_request("GET", "/trips/search")
    
    if response and response.status_code == 200:
        trips = response.json()
        print(f"✅ Trip search successful: Found {len(trips)} trips")
        if trips:
            print(f"   First trip: {trips[0]['origin']} → {trips[0]['destination']}")
    else:
        print(f"❌ Trip search failed: {response.status_code if response else 'No response'}")
    
    # Test trip search with filters
    print("\n4. Testing trip search with filters...")
    params = {
        "origin": "Manila",
        "destination": "Baguio",
        "vehicle_type": "bus"
    }
    response = make_request("GET", "/trips/search", params=params)
    
    if response and response.status_code == 200:
        trips = response.json()
        print(f"✅ Filtered trip search successful: Found {len(trips)} trips")
    else:
        print(f"❌ Filtered trip search failed: {response.status_code if response else 'No response'}")
    
    # Test get provider trips
    print("\n5. Testing get provider trips...")
    headers = {"Authorization": f"Bearer {provider_token}"}
    response = make_request("GET", "/trips/my", headers=headers)
    
    if response and response.status_code == 200:
        trips = response.json()
        print(f"✅ Provider trips retrieved: {len(trips)} trips")
    else:
        print(f"❌ Get provider trips failed: {response.status_code if response else 'No response'}")

def test_booking_system():
    """Test seat availability, booking creation, and cancellation"""
    global test_booking_id
    
    print("\n🎫 TESTING BOOKING SYSTEM")
    print("-" * 40)
    
    if not test_trip_id:
        print("❌ No test trip available for booking")
        return
    
    # Test get seat availability
    print("1. Testing seat availability...")
    response = make_request("GET", f"/trips/{test_trip_id}/seats")
    
    if response and response.status_code == 200:
        result = response.json()
        seats = result["seats"]
        available_count = sum(1 for seat in seats if seat["available"])
        print(f"✅ Seat availability retrieved: {available_count}/{len(seats)} seats available")
        
        # Find first available seat
        available_seat = next((seat for seat in seats if seat["available"]), None)
        if not available_seat:
            print("❌ No available seats for booking test")
            return
        seat_number = available_seat["number"]
        print(f"   Will book seat number: {seat_number}")
    else:
        print(f"❌ Get seat availability failed: {response.status_code if response else 'No response'}")
        return
    
    # Test booking creation
    print("\n2. Testing booking creation (as passenger)...")
    if not passenger_token:
        print("❌ No passenger token available")
        return
    
    booking_data = {
        "trip_id": test_trip_id,
        "seat_number": seat_number
    }
    
    headers = {"Authorization": f"Bearer {passenger_token}"}
    response = make_request("POST", "/bookings", booking_data, headers)
    
    if response and response.status_code == 200:
        result = response.json()
        test_booking_id = result["id"]
        print(f"✅ Booking created successfully: Seat {result['seat_number']}")
        print(f"   Booking ID: {test_booking_id}")
        print(f"   QR Code generated: {'✅' if result['qr_code'].startswith('data:image/png;base64,') else '❌'}")
    else:
        print(f"❌ Booking creation failed: {response.status_code if response else 'No response'}")
        if response:
            print(f"   Error: {response.text}")
        return
    
    # Test seat availability after booking
    print("\n3. Testing seat availability after booking...")
    response = make_request("GET", f"/trips/{test_trip_id}/seats")
    
    if response and response.status_code == 200:
        result = response.json()
        seats = result["seats"]
        booked_seat = next((seat for seat in seats if seat["number"] == seat_number), None)
        if booked_seat and not booked_seat["available"]:
            print("✅ Seat correctly marked as unavailable after booking")
        else:
            print("❌ Seat availability not updated after booking")
    else:
        print(f"❌ Get seat availability after booking failed: {response.status_code if response else 'No response'}")
    
    # Test duplicate booking (should fail)
    print("\n4. Testing duplicate booking (should fail)...")
    response = make_request("POST", "/bookings", booking_data, headers)
    
    if response and response.status_code == 400:
        print("✅ Duplicate booking correctly rejected")
    else:
        print(f"❌ Duplicate booking handling failed: {response.status_code if response else 'No response'}")
    
    # Test unauthorized booking (as provider)
    print("\n5. Testing unauthorized booking (as provider)...")
    headers = {"Authorization": f"Bearer {provider_token}"}
    booking_data_new = {
        "trip_id": test_trip_id,
        "seat_number": seat_number + 1
    }
    response = make_request("POST", "/bookings", booking_data_new, headers)
    
    if response and response.status_code == 403:
        print("✅ Provider correctly denied booking creation")
    else:
        print(f"❌ Authorization check failed: {response.status_code if response else 'No response'}")
    
    # Test get passenger bookings
    print("\n6. Testing get passenger bookings...")
    headers = {"Authorization": f"Bearer {passenger_token}"}
    response = make_request("GET", "/bookings/my", headers)
    
    if response and response.status_code == 200:
        bookings = response.json()
        print(f"✅ Passenger bookings retrieved: {len(bookings)} bookings")
        if bookings:
            booking = bookings[0]["booking"]
            trip = bookings[0]["trip"]
            print(f"   Booking: Seat {booking['seat_number']} on {trip['origin']} → {trip['destination']}")
    else:
        print(f"❌ Get passenger bookings failed: {response.status_code if response else 'No response'}")
    
    # Test booking cancellation
    print("\n7. Testing booking cancellation...")
    if not test_booking_id:
        print("❌ No booking ID available for cancellation")
        return
    
    response = make_request("PUT", f"/bookings/{test_booking_id}/cancel", headers=headers)
    
    if response and response.status_code == 200:
        print("✅ Booking cancelled successfully")
        
        # Verify seat availability increased
        response = make_request("GET", f"/trips/{test_trip_id}/seats")
        if response and response.status_code == 200:
            result = response.json()
            seats = result["seats"]
            cancelled_seat = next((seat for seat in seats if seat["number"] == seat_number), None)
            if cancelled_seat and cancelled_seat["available"]:
                print("✅ Seat correctly marked as available after cancellation")
            else:
                print("❌ Seat availability not updated after cancellation")
    else:
        print(f"❌ Booking cancellation failed: {response.status_code if response else 'No response'}")

def test_provider_features():
    """Test provider dashboard and check-in functionality"""
    
    print("\n👨‍💼 TESTING PROVIDER FEATURES")
    print("-" * 40)
    
    if not provider_token:
        print("❌ No provider token available")
        return
    
    # Create a new booking for check-in test
    print("1. Creating new booking for check-in test...")
    if not test_trip_id or not passenger_token:
        print("❌ Missing trip ID or passenger token")
        return
    
    # Get available seat
    response = make_request("GET", f"/trips/{test_trip_id}/seats")
    if not response or response.status_code != 200:
        print("❌ Cannot get seat availability")
        return
    
    seats = response.json()["seats"]
    available_seat = next((seat for seat in seats if seat["available"]), None)
    if not available_seat:
        print("❌ No available seats for check-in test")
        return
    
    # Create booking
    booking_data = {
        "trip_id": test_trip_id,
        "seat_number": available_seat["number"]
    }
    
    headers = {"Authorization": f"Bearer {passenger_token}"}
    response = make_request("POST", "/bookings", booking_data, headers)
    
    if not response or response.status_code != 200:
        print("❌ Cannot create booking for check-in test")
        return
    
    checkin_booking_id = response.json()["id"]
    print(f"✅ Test booking created: {checkin_booking_id}")
    
    # Test get provider bookings dashboard
    print("\n2. Testing provider bookings dashboard...")
    headers = {"Authorization": f"Bearer {provider_token}"}
    response = make_request("GET", "/provider/bookings", headers)
    
    if response and response.status_code == 200:
        bookings = response.json()
        print(f"✅ Provider bookings dashboard retrieved: {len(bookings)} bookings")
        if bookings:
            booking = bookings[0]
            print(f"   Booking: {booking['passenger']['name']} - Seat {booking['booking']['seat_number']}")
            print(f"   Status: {booking['booking']['status']}")
    else:
        print(f"❌ Get provider bookings failed: {response.status_code if response else 'No response'}")
    
    # Test unauthorized access to provider dashboard (as passenger)
    print("\n3. Testing unauthorized access to provider dashboard...")
    headers = {"Authorization": f"Bearer {passenger_token}"}
    response = make_request("GET", "/provider/bookings", headers)
    
    if response and response.status_code == 403:
        print("✅ Passenger correctly denied access to provider dashboard")
    else:
        print(f"❌ Authorization check failed: {response.status_code if response else 'No response'}")
    
    # Test passenger check-in
    print("\n4. Testing passenger check-in...")
    headers = {"Authorization": f"Bearer {provider_token}"}
    response = make_request("PUT", f"/provider/bookings/{checkin_booking_id}/checkin", headers=headers)
    
    if response and response.status_code == 200:
        print("✅ Passenger check-in successful")
        
        # Verify booking status updated
        response = make_request("GET", "/provider/bookings", headers)
        if response and response.status_code == 200:
            bookings = response.json()
            checked_booking = next((b for b in bookings if b["booking"]["id"] == checkin_booking_id), None)
            if checked_booking and checked_booking["booking"]["status"] == "boarded":
                print("✅ Booking status correctly updated to 'boarded'")
            else:
                print("❌ Booking status not updated after check-in")
    else:
        print(f"❌ Passenger check-in failed: {response.status_code if response else 'No response'}")
    
    # Test unauthorized check-in (as passenger)
    print("\n5. Testing unauthorized check-in (as passenger)...")
    headers = {"Authorization": f"Bearer {passenger_token}"}
    response = make_request("PUT", f"/provider/bookings/{checkin_booking_id}/checkin", headers=headers)
    
    if response and response.status_code == 403:
        print("✅ Passenger correctly denied check-in access")
    else:
        print(f"❌ Authorization check failed: {response.status_code if response else 'No response'}")

def test_error_handling():
    """Test various error scenarios"""
    
    print("\n⚠️  TESTING ERROR HANDLING")
    print("-" * 40)
    
    # Test invalid token
    print("1. Testing invalid token...")
    headers = {"Authorization": "Bearer invalid_token_here"}
    response = make_request("GET", "/trips/my", headers=headers)
    
    if response and response.status_code == 401:
        print("✅ Invalid token correctly rejected")
    else:
        print(f"❌ Invalid token handling failed: {response.status_code if response else 'No response'}")
    
    # Test missing token
    print("\n2. Testing missing token...")
    response = make_request("GET", "/trips/my")
    
    if response and response.status_code == 403:
        print("✅ Missing token correctly rejected")
    else:
        print(f"❌ Missing token handling failed: {response.status_code if response else 'No response'}")
    
    # Test non-existent trip booking
    print("\n3. Testing booking non-existent trip...")
    if passenger_token:
        booking_data = {
            "trip_id": "non-existent-trip-id",
            "seat_number": 1
        }
        headers = {"Authorization": f"Bearer {passenger_token}"}
        response = make_request("POST", "/bookings", booking_data, headers)
        
        if response and response.status_code == 404:
            print("✅ Non-existent trip booking correctly rejected")
        else:
            print(f"❌ Non-existent trip handling failed: {response.status_code if response else 'No response'}")
    
    # Test duplicate email registration
    print("\n4. Testing duplicate email registration...")
    duplicate_user = {
        "name": "Another Maria",
        "email": "maria.santos@email.com",  # Same email as before
        "password": "anotherpass123",
        "role": "passenger"
    }
    
    response = make_request("POST", "/auth/register", duplicate_user)
    
    if response and response.status_code == 400:
        print("✅ Duplicate email registration correctly rejected")
    else:
        print(f"❌ Duplicate email handling failed: {response.status_code if response else 'No response'}")

def run_all_tests():
    """Run all test suites"""
    print("🚀 STARTING TRIPLINK BACKEND API TESTS")
    print("=" * 60)
    
    try:
        test_authentication()
        test_trip_management()
        test_booking_system()
        test_provider_features()
        test_error_handling()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()