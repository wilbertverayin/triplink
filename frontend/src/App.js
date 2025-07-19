import React, { useState, useEffect, createContext, useContext } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Context for authentication
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    const storedToken = localStorage.getItem('token');
    
    if (storedUser && storedToken) {
      setUser(JSON.parse(storedUser));
      setToken(storedToken);
    }
    setLoading(false);
  }, []);

  const login = (userData, tokenData) => {
    setUser(userData);
    setToken(tokenData);
    localStorage.setItem('user', JSON.stringify(userData));
    localStorage.setItem('token', tokenData);
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('user');
    localStorage.removeItem('token');
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Components
const Navigation = () => {
  const { user, logout } = useAuth();

  return (
    <nav className="bg-blue-600 text-white p-4">
      <div className="container mx-auto flex justify-between items-center">
        <h1 className="text-2xl font-bold">🚌 TripLink</h1>
        {user && (
          <div className="flex items-center space-x-4">
            <span>Hello, {user.name}</span>
            <span className="bg-blue-800 px-2 py-1 rounded text-sm">
              {user.role === 'passenger' ? '👤 Passenger' : '🚐 Provider'}
            </span>
            <button 
              onClick={logout}
              className="bg-red-500 hover:bg-red-600 px-3 py-1 rounded"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </nav>
  );
};

const LoginForm = ({ isRegister, setIsRegister }) => {
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'passenger',
    phone: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isRegister ? '/auth/register' : '/auth/login';
      const payload = isRegister ? formData : { email: formData.email, password: formData.password };
      
      const response = await axios.post(`${API}${endpoint}`, payload);
      login(response.data.user, response.data.token);
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-100 to-blue-300 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
        <h2 className="text-3xl font-bold text-center text-gray-800 mb-8">
          {isRegister ? 'Join TripLink' : 'Welcome Back'}
        </h2>
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {isRegister && (
            <>
              <div>
                <input
                  type="text"
                  placeholder="Full Name"
                  required
                  className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                />
              </div>
              <div>
                <input
                  type="tel"
                  placeholder="Phone Number"
                  className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                />
              </div>
              <div>
                <select
                  className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.role}
                  onChange={(e) => setFormData({...formData, role: e.target.value})}
                >
                  <option value="passenger">👤 I'm a Passenger</option>
                  <option value="provider">🚐 I'm a Transport Provider</option>
                </select>
              </div>
            </>
          )}
          
          <div>
            <input
              type="email"
              placeholder="Email Address"
              required
              className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
            />
          </div>
          
          <div>
            <input
              type="password"
              placeholder="Password"
              required
              className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-4 rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? 'Please wait...' : (isRegister ? 'Create Account' : 'Sign In')}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => setIsRegister(!isRegister)}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            {isRegister ? 'Already have an account? Sign In' : "Don't have an account? Register"}
          </button>
        </div>
      </div>
    </div>
  );
};

const TripSearch = ({ onSelectTrip }) => {
  const [searchData, setSearchData] = useState({
    origin: '',
    destination: '',
    date: '',
    vehicle_type: ''
  });
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(false);

  const searchTrips = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      Object.entries(searchData).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      
      const response = await axios.get(`${API}/trips/search?${params}`);
      setTrips(response.data);
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const vehicleIcons = {
    bus: '🚌',
    van: '🚐',
    boat: '⛵',
    shuttle: '🚍'
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-bold mb-4">🔍 Search Transportation</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <input
            type="text"
            placeholder="From (Origin)"
            className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            value={searchData.origin}
            onChange={(e) => setSearchData({...searchData, origin: e.target.value})}
          />
          <input
            type="text"
            placeholder="To (Destination)"
            className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            value={searchData.destination}
            onChange={(e) => setSearchData({...searchData, destination: e.target.value})}
          />
          <input
            type="date"
            className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            value={searchData.date}
            onChange={(e) => setSearchData({...searchData, date: e.target.value})}
          />
          <select
            className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            value={searchData.vehicle_type}
            onChange={(e) => setSearchData({...searchData, vehicle_type: e.target.value})}
          >
            <option value="">All Vehicles</option>
            <option value="bus">🚌 Bus</option>
            <option value="van">🚐 Van</option>
            <option value="boat">⛵ Boat</option>
            <option value="shuttle">🚍 Shuttle</option>
          </select>
          <button
            onClick={searchTrips}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {trips.map(trip => (
          <div key={trip.id} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center space-x-4 mb-4">
                  <span className="text-3xl">{vehicleIcons[trip.vehicle_type]}</span>
                  <div>
                    <h4 className="text-xl font-bold">{trip.origin} → {trip.destination}</h4>
                    <p className="text-gray-600">{trip.vehicle_name}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="font-semibold">⏰ Departure:</span>
                    <p>{formatDateTime(trip.departure_time)}</p>
                  </div>
                  <div>
                    <span className="font-semibold">💺 Seats:</span>
                    <p>{trip.available_seats} / {trip.seat_capacity} available</p>
                  </div>
                  <div>
                    <span className="font-semibold">💰 Price:</span>
                    <p>₱{trip.price_per_seat}</p>
                  </div>
                  <div>
                    <span className="font-semibold">✨ Amenities:</span>
                    <p>{trip.amenities?.join(', ') || 'Basic'}</p>
                  </div>
                </div>
              </div>
              <button
                onClick={() => onSelectTrip(trip)}
                disabled={trip.available_seats === 0}
                className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-bold py-2 px-6 rounded-lg transition-colors"
              >
                {trip.available_seats === 0 ? 'Full' : 'Book Now'}
              </button>
            </div>
          </div>
        ))}
        
        {trips.length === 0 && !loading && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No trips found. Try adjusting your search criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
};

const SeatSelection = ({ trip, onBook, onBack }) => {
  const { token } = useAuth();
  const [seats, setSeats] = useState([]);
  const [selectedSeat, setSelectedSeat] = useState(null);
  const [loading, setLoading] = useState(false);
  const [bookingLoading, setBookingLoading] = useState(false);

  useEffect(() => {
    const fetchSeats = async () => {
      setLoading(true);
      try {
        const response = await axios.get(`${API}/trips/${trip.id}/seats`);
        setSeats(response.data.seats);
      } catch (err) {
        console.error('Error fetching seats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSeats();
  }, [trip.id]);

  const handleBooking = async () => {
    if (!selectedSeat) return;

    setBookingLoading(true);
    try {
      const response = await axios.post(
        `${API}/bookings`,
        {
          trip_id: trip.id,
          seat_number: selectedSeat
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      onBook(response.data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Booking failed');
    } finally {
      setBookingLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading seats...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold">🪑 Select Your Seat</h3>
        <button
          onClick={onBack}
          className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg"
        >
          ← Back to Search
        </button>
      </div>

      <div className="mb-6 p-4 bg-gray-100 rounded-lg">
        <h4 className="font-bold mb-2">{trip.origin} → {trip.destination}</h4>
        <p className="text-sm text-gray-600">
          {trip.vehicle_name} • ₱{trip.price_per_seat} per seat
        </p>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-6 max-w-md mx-auto">
        {seats.map(seat => (
          <button
            key={seat.number}
            onClick={() => seat.available && setSelectedSeat(seat.number)}
            className={`
              p-3 rounded-lg font-bold text-center transition-all
              ${seat.available 
                ? selectedSeat === seat.number
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-green-100 hover:bg-green-200 text-green-800'
                : 'bg-red-100 text-red-800 cursor-not-allowed'
              }
            `}
            disabled={!seat.available}
          >
            {seat.number}
          </button>
        ))}
      </div>

      <div className="text-center space-y-2 mb-6">
        <div className="flex justify-center space-x-6 text-sm">
          <div className="flex items-center">
            <div className="w-4 h-4 bg-green-100 rounded mr-2"></div>
            <span>Available</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-blue-600 rounded mr-2"></div>
            <span>Selected</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-red-100 rounded mr-2"></div>
            <span>Taken</span>
          </div>
        </div>
      </div>

      {selectedSeat && (
        <div className="text-center">
          <div className="bg-blue-50 p-4 rounded-lg mb-4">
            <p className="font-semibold">Seat {selectedSeat} selected</p>
            <p className="text-lg font-bold text-blue-600">Total: ₱{trip.price_per_seat}</p>
            <p className="text-sm text-gray-600 mt-2">
              💵 Payment: Cash on the day of travel<br/>
              ⏰ Please arrive 15 minutes early
            </p>
          </div>
          <button
            onClick={handleBooking}
            disabled={bookingLoading}
            className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-8 rounded-lg disabled:opacity-50"
          >
            {bookingLoading ? 'Booking...' : 'Confirm Booking'}
          </button>
        </div>
      )}
    </div>
  );
};

const BookingSuccess = ({ booking, trip, onNewSearch }) => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6 text-center">
      <div className="mb-6">
        <div className="text-6xl mb-4">✅</div>
        <h3 className="text-2xl font-bold text-green-600 mb-2">Booking Confirmed!</h3>
        <p className="text-gray-600">Your trip has been successfully booked</p>
      </div>

      <div className="bg-gray-50 rounded-lg p-6 mb-6">
        <h4 className="font-bold mb-4">📋 Booking Details</h4>
        <div className="text-left space-y-2">
          <p><strong>Route:</strong> {trip.origin} → {trip.destination}</p>
          <p><strong>Seat:</strong> #{booking.seat_number}</p>
          <p><strong>Vehicle:</strong> {trip.vehicle_name}</p>
          <p><strong>Price:</strong> ₱{trip.price_per_seat}</p>
          <p><strong>Booking ID:</strong> {booking.id}</p>
        </div>
      </div>

      <div className="mb-6">
        <h4 className="font-bold mb-4">📱 Your E-Ticket</h4>
        <div className="bg-white border-2 border-dashed border-gray-300 p-4 rounded-lg">
          <img 
            src={booking.qr_code} 
            alt="QR Code Ticket" 
            className="mx-auto mb-4 max-w-48"
          />
          <p className="text-sm text-gray-600">
            Show this QR code when boarding
          </p>
        </div>
      </div>

      <div className="bg-yellow-50 p-4 rounded-lg mb-6">
        <h5 className="font-bold text-yellow-800 mb-2">📍 Important Reminders</h5>
        <ul className="text-sm text-yellow-700 text-left list-disc list-inside space-y-1">
          <li>Arrive 15 minutes before departure</li>
          <li>Payment is cash-only at boarding</li>
          <li>Show your QR code to the conductor</li>
          <li>Keep your phone charged for the QR code</li>
        </ul>
      </div>

      <button
        onClick={onNewSearch}
        className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg"
      >
        Book Another Trip
      </button>
    </div>
  );
};

const MyBookings = () => {
  const { token } = useAuth();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchBookings = async () => {
      setLoading(true);
      try {
        const response = await axios.get(`${API}/bookings/my`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setBookings(response.data);
      } catch (err) {
        console.error('Error fetching bookings:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchBookings();
  }, [token]);

  const cancelBooking = async (bookingId) => {
    if (!window.confirm('Are you sure you want to cancel this booking?')) return;

    try {
      await axios.put(`${API}/bookings/${bookingId}/cancel`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Refresh bookings
      const response = await axios.get(`${API}/bookings/my`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBookings(response.data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Cancel failed');
    }
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'reserved': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      case 'boarded': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading your bookings...</div>;
  }

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold">🎫 My Bookings</h3>
      
      {bookings.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">No bookings yet</p>
        </div>
      ) : (
        bookings.map(({ booking, trip }) => (
          <div key={booking.id} className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h4 className="text-lg font-bold">{trip?.origin} → {trip?.destination}</h4>
                <p className="text-gray-600">{trip?.vehicle_name}</p>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(booking.status)}`}>
                {booking.status.toUpperCase()}
              </span>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
              <div>
                <span className="font-semibold">⏰ Departure:</span>
                <p>{formatDateTime(trip?.departure_time)}</p>
              </div>
              <div>
                <span className="font-semibold">💺 Seat:</span>
                <p>#{booking.seat_number}</p>
              </div>
              <div>
                <span className="font-semibold">💰 Price:</span>
                <p>₱{trip?.price_per_seat}</p>
              </div>
              <div>
                <span className="font-semibold">📋 Booking ID:</span>
                <p className="text-xs">{booking.id}</p>
              </div>
            </div>

            {booking.status === 'reserved' && (
              <div className="flex space-x-4">
                <div className="bg-gray-50 p-4 rounded-lg flex-1">
                  <p className="font-semibold mb-2">📱 Show QR Code at Boarding</p>
                  <img 
                    src={booking.qr_code} 
                    alt="QR Code" 
                    className="w-32 h-32 mx-auto"
                  />
                </div>
                <div className="flex flex-col justify-center">
                  <button
                    onClick={() => cancelBooking(booking.id)}
                    className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg"
                  >
                    Cancel Booking
                  </button>
                </div>
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
};

const ProviderDashboard = () => {
  const { token, user } = useAuth();
  const [trips, setTrips] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [newTrip, setNewTrip] = useState({
    origin: '',
    destination: '',
    departure_time: '',
    vehicle_type: 'bus',
    price_per_seat: '',
    seat_capacity: '',
    vehicle_name: '',
    amenities: []
  });

  useEffect(() => {
    fetchTrips();
    fetchBookings();
  }, []);

  const fetchTrips = async () => {
    try {
      const response = await axios.get(`${API}/trips/my`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTrips(response.data);
    } catch (err) {
      console.error('Error fetching trips:', err);
    }
  };

  const fetchBookings = async () => {
    try {
      const response = await axios.get(`${API}/provider/bookings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBookings(response.data);
    } catch (err) {
      console.error('Error fetching bookings:', err);
    }
  };

  const createTrip = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/trips`, {
        ...newTrip,
        price_per_seat: parseFloat(newTrip.price_per_seat),
        seat_capacity: parseInt(newTrip.seat_capacity)
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setShowCreateForm(false);
      setNewTrip({
        origin: '',
        destination: '',
        departure_time: '',
        vehicle_type: 'bus',
        price_per_seat: '',
        seat_capacity: '',
        vehicle_name: '',
        amenities: []
      });
      fetchTrips();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error creating trip');
    } finally {
      setLoading(false);
    }
  };

  const checkInPassenger = async (bookingId) => {
    try {
      await axios.put(`${API}/provider/bookings/${bookingId}/checkin`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchBookings();
    } catch (err) {
      alert(err.response?.data?.detail || 'Check-in failed');
    }
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const vehicleIcons = {
    bus: '🚌',
    van: '🚐',
    boat: '⛵',
    shuttle: '🚍'
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-bold">🚐 Provider Dashboard</h3>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
        >
          {showCreateForm ? 'Cancel' : '+ Add New Trip'}
        </button>
      </div>

      {showCreateForm && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h4 className="text-lg font-bold mb-4">🆕 Create New Trip</h4>
          <form onSubmit={createTrip} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Origin (From)"
                required
                className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                value={newTrip.origin}
                onChange={(e) => setNewTrip({...newTrip, origin: e.target.value})}
              />
              <input
                type="text"
                placeholder="Destination (To)"
                required
                className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                value={newTrip.destination}
                onChange={(e) => setNewTrip({...newTrip, destination: e.target.value})}
              />
              <input
                type="datetime-local"
                required
                className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                value={newTrip.departure_time}
                onChange={(e) => setNewTrip({...newTrip, departure_time: e.target.value})}
              />
              <select
                className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                value={newTrip.vehicle_type}
                onChange={(e) => setNewTrip({...newTrip, vehicle_type: e.target.value})}
              >
                <option value="bus">🚌 Bus</option>
                <option value="van">🚐 Van</option>
                <option value="boat">⛵ Boat</option>
                <option value="shuttle">🚍 Shuttle</option>
              </select>
              <input
                type="text"
                placeholder="Vehicle Name (e.g., Bus A1)"
                required
                className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                value={newTrip.vehicle_name}
                onChange={(e) => setNewTrip({...newTrip, vehicle_name: e.target.value})}
              />
              <input
                type="number"
                placeholder="Price per Seat (₱)"
                required
                className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                value={newTrip.price_per_seat}
                onChange={(e) => setNewTrip({...newTrip, price_per_seat: e.target.value})}
              />
              <input
                type="number"
                placeholder="Total Seats"
                required
                className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                value={newTrip.seat_capacity}
                onChange={(e) => setNewTrip({...newTrip, seat_capacity: e.target.value})}
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Trip'}
            </button>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h4 className="text-lg font-bold mb-4">📅 My Trips</h4>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {trips.map(trip => (
              <div key={trip.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-2xl">{vehicleIcons[trip.vehicle_type]}</span>
                  <div>
                    <h5 className="font-bold">{trip.origin} → {trip.destination}</h5>
                    <p className="text-sm text-gray-600">{trip.vehicle_name}</p>
                  </div>
                </div>
                <div className="text-sm space-y-1">
                  <p><strong>Departure:</strong> {formatDateTime(trip.departure_time)}</p>
                  <p><strong>Seats:</strong> {trip.available_seats}/{trip.seat_capacity} available</p>
                  <p><strong>Price:</strong> ₱{trip.price_per_seat}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h4 className="text-lg font-bold mb-4">🎫 Recent Bookings</h4>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {bookings.map(({ booking, passenger, trip }) => (
              <div key={booking.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h5 className="font-bold">{passenger?.name}</h5>
                    <p className="text-sm text-gray-600">{trip?.origin} → {trip?.destination}</p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${
                    booking.status === 'reserved' ? 'bg-green-100 text-green-800' :
                    booking.status === 'boarded' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {booking.status.toUpperCase()}
                  </span>
                </div>
                <div className="text-sm space-y-1 mb-3">
                  <p><strong>Seat:</strong> #{booking.seat_number}</p>
                  <p><strong>Contact:</strong> {passenger?.phone || passenger?.email}</p>
                </div>
                {booking.status === 'reserved' && (
                  <button
                    onClick={() => checkInPassenger(booking.id)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                  >
                    ✅ Check In
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const MainApp = () => {
  const { user } = useAuth();
  const [currentView, setCurrentView] = useState('search');
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [booking, setBooking] = useState(null);

  const handleTripSelect = (trip) => {
    setSelectedTrip(trip);
    setCurrentView('seats');
  };

  const handleBookingSuccess = (bookingData) => {
    setBooking(bookingData);
    setCurrentView('success');
  };

  const handleNewSearch = () => {
    setCurrentView('search');
    setSelectedTrip(null);
    setBooking(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100">
      <Navigation />
      
      <div className="container mx-auto px-4 py-8">
        {user.role === 'provider' ? (
          <ProviderDashboard />
        ) : (
          <div>
            <div className="mb-8 text-center">
              <div className="flex justify-center space-x-4 mb-6">
                <button
                  onClick={() => setCurrentView('search')}
                  className={`px-6 py-2 rounded-lg font-semibold ${
                    currentView === 'search' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-white text-blue-600 hover:bg-blue-50'
                  }`}
                >
                  🔍 Search Trips
                </button>
                <button
                  onClick={() => setCurrentView('bookings')}
                  className={`px-6 py-2 rounded-lg font-semibold ${
                    currentView === 'bookings' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-white text-blue-600 hover:bg-blue-50'
                  }`}
                >
                  🎫 My Bookings
                </button>
              </div>
            </div>

            {currentView === 'search' && (
              <TripSearch onSelectTrip={handleTripSelect} />
            )}
            
            {currentView === 'seats' && selectedTrip && (
              <SeatSelection 
                trip={selectedTrip} 
                onBook={handleBookingSuccess}
                onBack={handleNewSearch}
              />
            )}
            
            {currentView === 'success' && booking && selectedTrip && (
              <BookingSuccess 
                booking={booking} 
                trip={selectedTrip} 
                onNewSearch={handleNewSearch}
              />
            )}
            
            {currentView === 'bookings' && (
              <MyBookings />
            )}
          </div>
        )}
      </div>
    </div>
  );
};

function App() {
  const [isRegister, setIsRegister] = useState(false);

  return (
    <div className="App">
      <AuthProvider>
        <AuthContext.Consumer>
          {({ user, loading }) => {
            if (loading) {
              return (
                <div className="min-h-screen flex items-center justify-center">
                  <div className="text-xl">Loading...</div>
                </div>
              );
            }
            
            return user ? (
              <MainApp />
            ) : (
              <LoginForm isRegister={isRegister} setIsRegister={setIsRegister} />
            );
          }}
        </AuthContext.Consumer>
      </AuthProvider>
    </div>
  );
}

export default App;