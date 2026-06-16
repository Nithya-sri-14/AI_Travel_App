import sys
import os
# Ensure the parent directory is in the path so python can resolve 'backend' imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
from backend.database import db_connection
from backend.api import users, destinations, flights, weather, bookings, admin

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI(
    title="Smart Traveller API Platform",
    description="Enterprise-grade Backend API services with JWT security, Rate Limiting, Audit Trails, and RBAC.",
    version="2.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Security Headers Middleware (Governance)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Allow swagger UI styles/scripts to load normally, but keep default strict
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    logger.info("Initializing database schema...")
    db_connection.init_db()

# Include API routers
app.include_router(users.router)
app.include_router(destinations.router)
app.include_router(flights.router)
app.include_router(weather.router)
app.include_router(bookings.router)
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Enterprise Smart Traveller API is running securely",
        "docs_url": "/docs"
    }

@app.get("/api/stats")
def get_global_statistics():
    """
    Exposes aggregate KPIs for dashboard analytics.
    """
    try:
        total_users = db_connection.execute_read("SELECT COUNT(*) as count FROM users")[0]["count"]
        total_destinations = db_connection.execute_read("SELECT COUNT(*) as count FROM destinations")[0]["count"]
        total_bookings = db_connection.execute_read("SELECT COUNT(*) as count FROM bookings")[0]["count"]
        total_flights = db_connection.execute_read("SELECT COUNT(*) as count FROM flights")[0]["count"]
        
        # Determine popular destinations based on ratings and bookings
        popular_dest_query = """
            SELECT city_name, country, rating 
            FROM destinations 
            ORDER BY rating DESC, destination_id DESC 
            LIMIT 1
        """
        popular_res = db_connection.execute_read(popular_dest_query)
        popular_dest = f"{popular_res[0]['city_name']}, {popular_res[0]['country']}" if popular_res else "None"
        
        # Category breakdown for charts
        category_query = """
            SELECT category, COUNT(*) as count 
            FROM tourist_places 
            GROUP BY category
        """
        categories = db_connection.execute_read(category_query)
        
        # Booking trends: destinations with bookings
        booking_trends_query = """
            SELECT d.city_name, COUNT(b.booking_id) as booking_count
            FROM bookings b
            JOIN flights f ON b.flight_id = f.flight_id
            JOIN destinations d ON LOWER(f.destination_city) = LOWER(d.city_name)
            GROUP BY d.city_name
            ORDER BY booking_count DESC
            LIMIT 5
        """
        booking_trends = db_connection.execute_read(booking_trends_query)
        
        return {
            "total_users": total_users,
            "total_destinations": total_destinations,
            "total_bookings": total_bookings,
            "total_flights": total_flights,
            "popular_destination": popular_dest,
            "category_distribution": categories,
            "booking_trends": booking_trends
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return {
            "total_users": 0,
            "total_destinations": 0,
            "total_bookings": 0,
            "total_flights": 0,
            "popular_destination": "None",
            "category_distribution": [],
            "booking_trends": []
        }
