# Smart Traveller Platform

A premium, enterprise-ready full-stack Travel Intelligence Platform built with Python, FastAPI, and Streamlit. The application features destination searching, attraction mapping, weather forecasting, flight search and price comparison, day-wise itineraries, booking tracking, and dashboard analytics.

---

## Project Structure
```
AI TRAVEL APP/
├── backend/
│   ├── main.py                     # FastAPI Application Entrypoint
│   ├── config.py                   # Environment configuration & API credentials
│   ├── requirements.txt            # Backend dependencies
│   ├── database/
│   │   ├── db_connection.py        # Database adapter (MySQL/SQLite dual support)
│   │   └── schema.sql              # SQL Schema for database tables
│   ├── api/
│   │   ├── users.py                # Users & Authentication Router
│   │   ├── destinations.py         # Destinations & Places Router (Google Places / OpenStreetMap fallback)
│   │   ├── flights.py              # Flights Router (Strictly Duffel API)
│   │   ├── bookings.py             # Bookings Router
│   │   └── weather.py              # Weather Router (OpenWeatherMap / Open-Meteo fallback)
│   └── services/
│       ├── itinerary_service.py    # Rule-based itinerary generator
│       ├── recommendation_engine.py# Rule-based package recommender
│       └── audit_service.py        # System audit trail logger
│
├── frontend/
│   ├── app.py                      # Main Streamlit Entrypoint
│   ├── requirements.txt            # Frontend dependencies
│   ├── pages/
│   │   ├── 1_Dashboard.py          # Analytics dashboard (KPIs, Charts)
│   │   ├── 2_Destinations.py       # Search, attractions list, maps, itinerary
│   │   ├── 3_Flights.py            # Search flights, compare prices, check out
│   │   └── 4_Profile.py            # User registration/login & bookings log
│   └── assets/
│       └── style.css               # Premium CSS styles
│
└── README.md                       # Setup & Configuration Guide
```

---

## Quick Start (Zero Config SQLite Fallback)

### Step 1: Install Dependencies
Open your terminal and run:
```bash
# Setup backend dependencies
cd backend
pip install -r requirements.txt

# Setup frontend dependencies
cd ../frontend
pip install -r requirements.txt
```

### Step 2: Start the FastAPI Backend
```bash
# Navigate to the workspace root
cd "/Users/user/Documents/AI TRAVEL APP"
# Activate the virtual environment
source venv/bin/activate
# Run uvicorn referencing the backend module from the root
uvicorn backend.main:app --reload --port 8000
```
This automatically initializes the SQLite database file `traveller.db` inside the `backend/` directory on startup.

### Step 3: Start the Streamlit Frontend
In a new terminal window:
```bash
cd "/Users/user/Documents/AI TRAVEL APP"
source venv/bin/activate
cd frontend
streamlit run app.py
```
This will open the application in your default web browser at `http://localhost:8501`.

---

## Configuring the `.env` File

To run the application with live connections (specifically the Duffel Flight Search) and premium databases, create a `.env` file in the `backend/` directory with the following variables:

```env
# Database Settings (Use 'sqlite' for zero-config, or 'mysql' for MySQL server)
DB_TYPE=sqlite

# MySQL Settings (Only used if DB_TYPE=mysql)
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=traveller_db

# Enterprise JWT security secret (Use any random secure string)
JWT_SECRET_KEY=your_super_secret_jwt_signkey_12345

# Duffel API Access Token (Required for Flight Searches)
# Access tokens can be generated from your Duffel Developer Dashboard: https://duffel.com/dashboard
# In test mode, tokens start with 'duffel_test_'
DUFFEL_ACCESS_TOKEN=duffel_test_your_actual_token_here

# Google Places API Key (Optional. If unconfigured, falls back to OpenStreetMap geocoding and Overpass APIs)
GOOGLE_PLACES_API_KEY=

# OpenWeatherMap API Key (Optional. If unconfigured, falls back to Open-Meteo API)
OPENWEATHER_API_KEY=
```

*Note: Make sure your local MySQL server is running before starting the backend if you set `DB_TYPE=mysql`.*

---

## Running inside VS Code
The workspace includes a `.vscode/launch.json` configuration. Simply open the **AI TRAVEL APP** folder in VS Code, go to the **Run & Debug** tab, select **Launch Backend & Frontend**, and click the green Play button.
