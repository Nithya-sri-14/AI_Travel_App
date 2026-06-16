from fastapi import APIRouter, Query, HTTPException, Request, status
import requests
import logging
from backend import config
from backend.database import db_connection
from backend.services import audit_service

router = APIRouter(prefix="/api/weather", tags=["Weather"])
logger = logging.getLogger("weather_api")

# WMO Weather Code to Condition mapping
WMO_WEATHER_CODES = {
    0: "Sunny",
    1: "Partly Cloudy", 2: "Partly Cloudy", 3: "Cloudy",
    45: "Foggy", 48: "Foggy",
    51: "Light Rain", 53: "Light Rain", 55: "Light Rain",
    61: "Rain", 63: "Rain", 65: "Heavy Rain",
    71: "Snow", 73: "Snow", 75: "Heavy Snow",
    80: "Light Rain", 81: "Rain", 82: "Heavy Rain",
    95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm"
}

def geocode_city_nominatim(city_name: str) -> tuple:
    """
    Geocodes city name to (lat, lon, country) using OpenStreetMap Nominatim (Keyless).
    """
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "SmartTravellerApp/1.0"}
    params = {"city": city_name, "format": "json", "limit": 1}
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        res_data = res.json()
        if res_data:
            item = res_data[0]
            lat = float(item["lat"])
            lon = float(item["lon"])
            display_name = item.get("display_name", "")
            country = display_name.split(",")[-1].strip()
            return lat, lon, country
    except Exception as e:
        logger.error(f"Nominatim Geocoding error: {e}")
    return None, None, None

def fetch_open_meteo(city_name: str, client_ip: str):
    """
    Fetches real-time weather from Open-Meteo API (Keyless / Free).
    """
    # 1. Get coordinates from DB if city exists, otherwise query Nominatim
    lat, lon = None, None
    dest = db_connection.execute_read(
        "SELECT tp.latitude, tp.longitude FROM tourist_places tp JOIN destinations d ON tp.destination_id = d.destination_id WHERE LOWER(d.city_name) = %s LIMIT 1",
        (city_name.lower(),)
    )
    if dest:
        lat = dest[0]["latitude"]
        lon = dest[0]["longitude"]
    else:
        lat, lon, _ = geocode_city_nominatim(city_name)
        
    if not lat or not lon:
        # Fallback coordinates (London)
        lat, lon = 51.5074, -0.1278
        
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,precipitation_probability_max",
        "timezone": "auto"
    }
    
    try:
        res = requests.get(url, params=params, timeout=5)
        res_data = res.json()
        
        current = res_data.get("current", {})
        daily = res_data.get("daily", {})
        
        curr_code = current.get("weather_code", 0)
        condition = WMO_WEATHER_CODES.get(curr_code, "Sunny")
        
        # Parse 5-day forecast
        forecast = []
        time_list = daily.get("time", [])
        temp_max_list = daily.get("temperature_2m_max", [])
        code_list = daily.get("weather_code", [])
        rain_prob_list = daily.get("precipitation_probability_max", [])
        
        for idx in range(min(5, len(time_list))):
            fc_code = code_list[idx] if idx < len(code_list) else 0
            forecast.append({
                "date": time_list[idx],
                "temp": round(temp_max_list[idx]) if idx < len(temp_max_list) else 20,
                "condition": WMO_WEATHER_CODES.get(fc_code, "Sunny"),
                "rain_prob": int(rain_prob_list[idx]) if idx < len(rain_prob_list) else 10
            })
            
        return {
            "city_name": city_name.capitalize(),
            "temperature": round(current.get("temperature_2m", 20)),
            "condition": condition,
            "humidity": current.get("relative_humidity_2m", 60),
            "wind_speed": current.get("wind_speed_10m", 10.0),
            "rain_probability": forecast[0]["rain_prob"] if forecast else 10,
            "forecast": forecast
        }
    except Exception as e:
        logger.error(f"Open-Meteo weather fetch error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Open-Meteo weather request failed: {e}"
        )

def fetch_openweather(city_name: str, client_ip: str):
    """
    Calls OpenWeatherMap API (Premium / Key required).
    """
    api_key = config.OPENWEATHER_API_KEY
    try:
        current_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
        curr_res = requests.get(current_url, timeout=5).json()
        if curr_res.get("cod") != 200:
            return None
            
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city_name}&appid={api_key}&units=metric"
        fore_res = requests.get(forecast_url, timeout=5).json()
        if fore_res.get("cod") != "200":
            return None
            
        forecast_list = []
        seen_dates = set()
        for item in fore_res.get("list", []):
            dt_txt = item.get("dt_txt", "")
            date = dt_txt.split(" ")[0]
            if date not in seen_dates and ("12:00:00" in dt_txt or len(seen_dates) < 5):
                seen_dates.add(date)
                forecast_list.append({
                    "date": date,
                    "temp": round(item["main"]["temp"]),
                    "condition": item["weather"][0]["main"],
                    "rain_prob": round(item.get("pop", 0) * 100)
                })
                
        rain_prob = 0
        if "rain" in curr_res:
            rain_prob = 80
        elif "clouds" in curr_res:
            rain_prob = curr_res["clouds"].get("all", 0) // 2
            
        return {
            "city_name": city_name.capitalize(),
            "temperature": round(curr_res["main"]["temp"]),
            "condition": curr_res["weather"][0]["main"],
            "humidity": curr_res["main"]["humidity"],
            "wind_speed": curr_res["wind"]["speed"],
            "rain_probability": rain_prob,
            "forecast": forecast_list[:5]
        }
    except Exception as e:
        logger.error(f"Error fetching from OpenWeather API: {e}")
        return None

@router.get("")
def get_weather(request: Request, city: str = Query(..., description="City name to fetch weather for")):
    city_clean = city.strip().lower()
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # Check if Premium OpenWeather is configured
    if config.OPENWEATHER_API_KEY:
        logger.info("Fetching real weather from OpenWeatherMap API...")
        weather_data = fetch_openweather(city_clean, client_ip)
        if weather_data:
            return {"status": "success", "source": "api_openweather", "data": weather_data}
            
    # Keyless Fallback: Use Open-Meteo
    logger.info("OpenWeatherMap unconfigured or failed. Fetching real-time weather from Open-Meteo (Keyless)...")
    weather_data = fetch_open_meteo(city_clean, client_ip)
    return {"status": "success", "source": "api_openmeteo", "data": weather_data}
