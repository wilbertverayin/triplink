from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import bcrypt
import jwt
import qrcode
from io import BytesIO
import base64
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is required")
ALGORITHM = "HS256"

# Security
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI(title="TripLink API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class UserRole(str, Enum):
    PASSENGER = "passenger"
    PROVIDER = "provider"

class BookingStatus(str, Enum):
    RESERVED = "reserved"
    CANCELLED = "cancelled"
    BOARDED = "boarded"
    NO_SHOW = "no_show"

class VehicleType(str, Enum):
    BUS = "bus"
    VAN = "van"
    BOAT = "boat"
    SHUTTLE = "shuttle"

# Models
class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role: UserRole
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    role: UserRole
    phone: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TripCreate(BaseModel):
    origin: str
    destination: str
    departure_time: datetime
    vehicle_type: VehicleType
    price_per_seat: float
    seat_capacity: int
    amenities: Optional[List[str]] = []
    vehicle_name: str

class Trip(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: str
    origin: str
    destination: str
    departure_time: datetime
    vehicle_type: VehicleType
    price_per_seat: float
    seat_capacity: int
    available_seats: int
    amenities: Optional[List[str]] = []
    vehicle_name: str
    status: str = "open"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TripSearch(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    date: Optional[str] = None
    vehicle_type: Optional[VehicleType] = None

class BookingCreate(BaseModel):
    trip_id: str
    seat_number: int

class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    passenger_id: str
    trip_id: str
    seat_number: int
    status: BookingStatus = BookingStatus.RESERVED
    qr_code: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_jwt_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_jwt_token(credentials.credentials)
    user = await db.users.find_one({"id": payload["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

def generate_qr_code(booking_data: str) -> str:
    """Generate QR code and return as base64 string"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(booking_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# Authentication routes
@api_router.post("/auth/register")
async def register(user_data: UserRegister):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = hash_password(user_data.password)
    user = User(
        name=user_data.name,
        email=user_data.email,
        role=user_data.role,
        phone=user_data.phone
    )
    
    user_doc = user.dict()
    user_doc["password"] = hashed_password
    
    await db.users.insert_one(user_doc)
    
    # Create JWT token
    token = create_jwt_token(user.id, user.email, user.role)
    
    return {"user": user, "token": token}

@api_router.post("/auth/login")
async def login(login_data: UserLogin):
    # Find user
    user_doc = await db.users.find_one({"email": login_data.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(login_data.password, user_doc["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = User(**user_doc)
    token = create_jwt_token(user.id, user.email, user.role)
    
    return {"user": user, "token": token}

# Trip routes
@api_router.get("/trips/search")
async def search_trips(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    date: Optional[str] = None,
    vehicle_type: Optional[str] = None
):
    # Build query
    query = {"status": "open"}
    
    if origin:
        query["origin"] = {"$regex": origin, "$options": "i"}
    if destination:
        query["destination"] = {"$regex": destination, "$options": "i"}
    if date:
        # Parse date and find trips on that day
        search_date = datetime.fromisoformat(date)
        start_of_day = search_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = search_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        query["departure_time"] = {"$gte": start_of_day, "$lte": end_of_day}
    if vehicle_type:
        query["vehicle_type"] = vehicle_type
    
    trips = await db.trips.find(query).to_list(100)
    return [Trip(**trip) for trip in trips]

@api_router.post("/trips", dependencies=[Depends(get_current_user)])
async def create_trip(trip_data: TripCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.PROVIDER:
        raise HTTPException(status_code=403, detail="Only providers can create trips")
    
    trip = Trip(
        provider_id=current_user.id,
        origin=trip_data.origin,
        destination=trip_data.destination,
        departure_time=trip_data.departure_time,
        vehicle_type=trip_data.vehicle_type,
        price_per_seat=trip_data.price_per_seat,
        seat_capacity=trip_data.seat_capacity,
        available_seats=trip_data.seat_capacity,
        amenities=trip_data.amenities,
        vehicle_name=trip_data.vehicle_name
    )
    
    await db.trips.insert_one(trip.dict())
    return trip

@api_router.get("/trips/my", dependencies=[Depends(get_current_user)])
async def get_my_trips(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.PROVIDER:
        trips = await db.trips.find({"provider_id": current_user.id}).to_list(100)
    else:
        # Get passenger bookings and their trips
        bookings = await db.bookings.find({"passenger_id": current_user.id}).to_list(100)
        trip_ids = [booking["trip_id"] for booking in bookings]
        trips = await db.trips.find({"id": {"$in": trip_ids}}).to_list(100)
    
    return [Trip(**trip) for trip in trips]

@api_router.get("/trips/{trip_id}/seats")
async def get_trip_seats(trip_id: str):
    trip = await db.trips.find_one({"id": trip_id})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Get booked seats
    bookings = await db.bookings.find({"trip_id": trip_id, "status": {"$ne": "cancelled"}}).to_list(100)
    booked_seats = [booking["seat_number"] for booking in bookings]
    
    # Generate seat layout
    seats = []
    for i in range(1, trip["seat_capacity"] + 1):
        seats.append({
            "number": i,
            "available": i not in booked_seats
        })
    
    return {"seats": seats, "trip": Trip(**trip)}

# Booking routes
@api_router.post("/bookings", dependencies=[Depends(get_current_user)])
async def create_booking(booking_data: BookingCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.PASSENGER:
        raise HTTPException(status_code=403, detail="Only passengers can make bookings")
    
    # Check if trip exists
    trip = await db.trips.find_one({"id": booking_data.trip_id})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Check if seat is available
    existing_booking = await db.bookings.find_one({
        "trip_id": booking_data.trip_id,
        "seat_number": booking_data.seat_number,
        "status": {"$ne": "cancelled"}
    })
    if existing_booking:
        raise HTTPException(status_code=400, detail="Seat is already booked")
    
    # Create booking
    qr_data = f"TRIPLINK-{booking_data.trip_id}-{current_user.id}-{booking_data.seat_number}"
    qr_code = generate_qr_code(qr_data)
    
    booking = Booking(
        passenger_id=current_user.id,
        trip_id=booking_data.trip_id,
        seat_number=booking_data.seat_number,
        qr_code=qr_code
    )
    
    await db.bookings.insert_one(booking.dict())
    
    # Update available seats
    await db.trips.update_one(
        {"id": booking_data.trip_id},
        {"$inc": {"available_seats": -1}}
    )
    
    return booking

@api_router.get("/bookings/my", dependencies=[Depends(get_current_user)])
async def get_my_bookings(current_user: User = Depends(get_current_user)):
    bookings = await db.bookings.find({"passenger_id": current_user.id}).to_list(100)
    
    # Get trip details for each booking
    result = []
    for booking_doc in bookings:
        trip = await db.trips.find_one({"id": booking_doc["trip_id"]})
        booking = Booking(**booking_doc)
        result.append({
            "booking": booking,
            "trip": Trip(**trip) if trip else None
        })
    
    return result

@api_router.put("/bookings/{booking_id}/cancel", dependencies=[Depends(get_current_user)])
async def cancel_booking(booking_id: str, current_user: User = Depends(get_current_user)):
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking["passenger_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if booking["status"] != "reserved":
        raise HTTPException(status_code=400, detail="Booking cannot be cancelled")
    
    # Update booking status
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"status": "cancelled"}}
    )
    
    # Increase available seats
    await db.trips.update_one(
        {"id": booking["trip_id"]},
        {"$inc": {"available_seats": 1}}
    )
    
    return {"message": "Booking cancelled successfully"}

# Provider dashboard routes
@api_router.get("/provider/bookings", dependencies=[Depends(get_current_user)])
async def get_provider_bookings(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.PROVIDER:
        raise HTTPException(status_code=403, detail="Only providers can access this")
    
    # Get provider's trips
    trips = await db.trips.find({"provider_id": current_user.id}).to_list(100)
    trip_ids = [trip["id"] for trip in trips]
    
    # Get bookings for these trips
    bookings = await db.bookings.find({"trip_id": {"$in": trip_ids}}).to_list(100)
    
    # Get passenger details
    result = []
    for booking_doc in bookings:
        passenger = await db.users.find_one({"id": booking_doc["passenger_id"]})
        trip = await db.trips.find_one({"id": booking_doc["trip_id"]})
        
        booking = Booking(**booking_doc)
        result.append({
            "booking": booking,
            "passenger": User(**passenger) if passenger else None,
            "trip": Trip(**trip) if trip else None
        })
    
    return result

@api_router.put("/provider/bookings/{booking_id}/checkin", dependencies=[Depends(get_current_user)])
async def checkin_passenger(booking_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.PROVIDER:
        raise HTTPException(status_code=403, detail="Only providers can check in passengers")
    
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Verify this is provider's trip
    trip = await db.trips.find_one({"id": booking["trip_id"], "provider_id": current_user.id})
    if not trip:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update booking status
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"status": "boarded"}}
    )
    
    return {"message": "Passenger checked in successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()