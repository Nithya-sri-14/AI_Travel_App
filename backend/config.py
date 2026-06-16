import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Application Settings
APP_NAME = "Smart Traveller Platform Backend"
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()  # "sqlite" or "mysql"
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "traveller_db")
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "traveller.db")

# External APIs Configuration
# Crucial keys must be configured in .env for live operations
FLIGHT_PROVIDER = os.getenv("FLIGHT_PROVIDER", "auto").lower()  # 'auto', 'aviationstack', or 'simulated'
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# Aviationstack Credentials
AVIATIONSTACK_ACCESS_KEY = os.getenv("AVIATIONSTACK_ACCESS_KEY", "")

