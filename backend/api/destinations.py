from fastapi import APIRouter, HTTPException, Query, Depends, Request, status
from pydantic import BaseModel, constr
import requests
import logging
import copy
import random
from backend import config
from backend.database import db_connection
from backend.services import itinerary_service, recommendation_engine
from backend.utils.rate_limiter import rate_limit_dependency
from backend.services import audit_service
from backend.api import users
from backend.services.destinations_registry import POPULAR_CITIES_REGISTRY

router = APIRouter(prefix="/api/destinations", tags=["Destinations"])
logger = logging.getLogger("destinations_api")

class BudgetRequest(BaseModel):
    budget: float
    city_name: constr(min_length=2, max_length=50, pattern=r"^[a-zA-Z\s\-]+$")
    country: constr(min_length=2, max_length=50, pattern=r"^[a-zA-Z\s\-]+$")

class ItineraryRequest(BaseModel):
    destination_id: int
    days: int = 3

def geocode_city_nominatim(city_name: str) -> tuple:
    """Geocodes city name to (lat, lon, country, display_name) using Nominatim."""
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "SmartTravellerApp/1.0"}
    params = {"q": city_name, "format": "json", "limit": 1}
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        res_data = res.json()
        if res_data:
            item = res_data[0]
            lat = float(item["lat"])
            lon = float(item["lon"])
            display_name = item.get("display_name", "")
            country = display_name.split(",")[-1].strip()
            return lat, lon, country, display_name
    except Exception as e:
        logger.error(f"Nominatim Geocoding error: {e}")
    return None, None, None, None

def fetch_overpass_places(lat: float, lon: float, city_name: str):
    """
    Fetches tourist attractions inside a 10km radius using OpenStreetMap Overpass API (Keyless).
    Explicitly filters out lodging and hotels.
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    headers = {"User-Agent": "SmartTravellerApp/1.0 (contact: developer@smarttraveller.org)"}
    # Query specific tourist/historical categories, avoiding broad searches that grab hotels
    query = f"""
    [out:json][timeout:15];
    (
      nwr(around:10000,{lat},{lon})["tourism"="attraction"];
      nwr(around:10000,{lat},{lon})["tourism"="museum"];
      nwr(around:10000,{lat},{lon})["tourism"="viewpoint"];
      nwr(around:10000,{lat},{lon})["tourism"="theme_park"];
      nwr(around:10000,{lat},{lon})["tourism"="zoo"];
      nwr(around:10000,{lat},{lon})["amenity"="place_of_worship"];
      nwr(around:10000,{lat},{lon})["historical"];
    );
    out center 35;
    """
    try:
        res = requests.post(overpass_url, headers=headers, data={"data": query}, timeout=12)
        if res.status_code != 200:
            logger.warning(f"Overpass API returned status code {res.status_code}: {res.text[:200]}")
            return []
            
        res_data = res.json()
        
        places = []
        seen_names = set()
        for element in res_data.get("elements", []):
            tags = element.get("tags", {})
            name = tags.get("name")
            if not name or name in seen_names:
                continue
                
            # Filter out lodging / hotels
            tourism = tags.get("tourism", "")
            if tourism in ["hotel", "motel", "hostel", "guest_house", "apartment", "chalet", "camp_site", "caravan_site"]:
                continue
                
            seen_names.add(name)
            
            # Extract coordinates
            el_lat = element.get("lat")
            el_lon = element.get("lon")
            if not el_lat or not el_lon:
                center = element.get("center", {})
                el_lat = center.get("lat")
                el_lon = center.get("lon")
                
            if not el_lat or not el_lon:
                continue
            
            # Category Mapping
            amenity = tags.get("amenity", "")
            religion = tags.get("religion", "")
            
            category = "Historical"
            if tourism in ["museum", "art_gallery"]:
                category = "Museum"
            elif amenity == "place_of_worship" or religion:
                category = "Temple"
            elif tourism in ["beach_resort", "theme_park", "zoo"]:
                category = "Adventure"
            elif tourism in ["beach", "viewpoint"]:
                category = "Beach"
                
            places.append({
                "place_name": name,
                "category": category,
                "rating": round(4.0 + (element.get("id", 0) % 10) / 10.0, 1), # Stable pseudo-random rating
                "latitude": el_lat,
                "longitude": el_lon,
                "address": tags.get("addr:street", f"Near {city_name.capitalize()}")
            })
            
        return places
    except Exception as e:
        logger.error(f"Overpass API error: {e}")
        return []

def fetch_google_places(city_name: str, client_ip: str):
    """Calls real Google Places API to find tourist attractions."""
    try:
        geocode_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={city_name}&key={config.GOOGLE_PLACES_API_KEY}"
        geo_res = requests.get(geocode_url, timeout=5).json()
        if not geo_res.get("results"):
            return None
            
        city_result = geo_res["results"][0]
        formatted_address = city_result.get("formatted_address", "")
        country = formatted_address.split(",")[-1].strip()
        
        query = f"top tourist attractions in {city_name}"
        search_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={config.GOOGLE_PLACES_API_KEY}"
        places_res = requests.get(search_url, timeout=5).json()
        
        places = []
        for result in places_res.get("results", [])[:30]:
            types = result.get("types", [])
            # Filter out lodging / hotels
            if any(t in ["lodging", "hotel", "motel", "hostel", "guest_house", "spa", "resort"] for t in types):
                continue
                
            category = "Historical"
            if any(t in ["museum", "art_gallery"] for t in types):
                category = "Museum"
            elif any(t in ["place_of_worship", "church", "hindu_temple", "synagogue", "mosque"] for t in types):
                category = "Temple"
            elif any(t in ["beach", "aquarium", "lake", "natural_feature"] for t in types):
                category = "Beach"
            elif any(t in ["amusement_park", "zoo", "park", "campground"] for t in types):
                category = "Adventure"
                
            places.append({
                "place_name": result.get("name"),
                "category": category,
                "rating": result.get("rating", 4.0),
                "latitude": result.get("geometry", {}).get("location", {}).get("lat", 0.0),
                "longitude": result.get("geometry", {}).get("location", {}).get("lng", 0.0),
                "address": result.get("formatted_address", "")
            })
            
        return {
            "city_name": city_name.capitalize(),
            "country": country,
            "rating": city_result.get("rating", 4.5),
            "description": f"Beautiful city of {city_name.capitalize()} known for its tourist spots, rich culture, and landmarks.",
            "places": places
        }
    except Exception as e:
        logger.error(f"Error fetching from Google Places API: {e}")
        return None

@router.get("/search", dependencies=[Depends(rate_limit_dependency("search"))])
def search_destination(request: Request, city: str = Query(..., description="City name to search")):
    city_clean = city.strip().lower()
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # Check if exists in DB
    dest = db_connection.execute_read(
        "SELECT * FROM destinations WHERE LOWER(city_name) = %s",
        (city_clean,)
    )
    
    if dest:
        dest_data = dest[0]
        # Query cached tourist places using RANDOM to change every time
        _, is_sqlite = db_connection.get_connection()
        random_func = "RANDOM()" if is_sqlite else "RAND()"
        
        places = db_connection.execute_read(
            f"SELECT * FROM tourist_places WHERE destination_id = %s ORDER BY {random_func} LIMIT 8",
            (dest_data["destination_id"],)
        )
        dest_data["places"] = places
        audit_service.log_action(None, "destination_search_db", client_ip, "Success", f"City: {city_clean}")
        return {"status": "success", "source": "database", "data": dest_data}
        
    # Check popular cities registry for 100% accurate real-world fallback
    api_data = None
    if city_clean in POPULAR_CITIES_REGISTRY:
        logger.info(f"Loading {city_clean} from verified popular cities registry...")
        api_data = copy.deepcopy(POPULAR_CITIES_REGISTRY[city_clean])
        
    # Not in DB and not in registry, fetch from Google API if key is present
    if not api_data and config.GOOGLE_PLACES_API_KEY:
        logger.info(f"Fetching {city} from Google Places API...")
        api_data = fetch_google_places(city_clean, client_ip)
        
    # Keyless Fallback: Use OpenStreetMap (Nominatim + Overpass)
    if not api_data:
        logger.info(f"Google Places unconfigured or failed. Querying OpenStreetMap for {city_clean} (Keyless)...")
        lat, lon, country, display_name = geocode_city_nominatim(city_clean)
        
        if not lat or not lon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"City '{city_clean}' could not be located on the map. Please check spelling."
            )
            
        places = fetch_overpass_places(lat, lon, city_clean)
        
        # If no attractions found, add a generic downtown attraction to let mapping work
        if not places:
            places.append({
                "place_name": f"Downtown {city_clean.capitalize()}",
                "category": "Historical",
                "rating": 4.5,
                "latitude": lat,
                "longitude": lon,
                "address": f"City Center, {country}"
            })
            
        api_data = {
            "city_name": city_clean.capitalize(),
            "country": country,
            "rating": 4.5,
            "description": f"A historic and scenic destination located in {country}. Explored via OpenStreetMap.",
            "places": places
        }
        
    # Save destination to DB
    dest_id = db_connection.execute_query(
        "INSERT INTO destinations (city_name, country, rating, description) VALUES (%s, %s, %s, %s)",
        (api_data["city_name"], api_data["country"], api_data["rating"], api_data["description"])
    )
    
    # Save all fetched places to DB
    for place in api_data["places"]:
        db_connection.execute_query(
            "INSERT INTO tourist_places (destination_id, place_name, category, rating, latitude, longitude, address) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (dest_id, place["place_name"], place["category"], place["rating"], place["latitude"], place["longitude"], place["address"])
        )
        
    # Return a randomized subset of 8 places
    random.shuffle(api_data["places"])
    api_data["places"] = api_data["places"][:8]
    
    # Re-fetch populated object
    api_data["destination_id"] = dest_id
    for idx, p in enumerate(api_data["places"]):
        p["destination_id"] = dest_id
        
    audit_service.log_action(None, "destination_search_created", client_ip, "Success", f"City: {city_clean} | Saved ID: {dest_id}")
    return {"status": "success", "source": "api", "data": api_data}

@router.get("/all")
def get_all_cached_destinations():
    destinations = db_connection.execute_read("SELECT * FROM destinations")
    return {"status": "success", "data": destinations}

@router.post("/recommendations")
def get_recommendations(req: BudgetRequest):
    dest = db_connection.execute_read(
        "SELECT * FROM destinations WHERE LOWER(city_name) = %s",
        (req.city_name.lower(),)
    )
    categories = []
    if dest:
        places = db_connection.execute_read(
            "SELECT DISTINCT category FROM tourist_places WHERE destination_id = %s",
            (dest[0]["destination_id"],)
        )
        categories = [p["category"] for p in places]
        
    # Get weather condition dynamically from Open-Meteo or OpenWeather
    weather_cond = "Sunny"
    lat, lon, _, _ = geocode_city_nominatim(req.city_name)
    if lat and lon:
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=weather_code"
            res = requests.get(url, timeout=3).json()
            code = res.get("current", {}).get("weather_code", 0)
            from backend.api.weather import WMO_WEATHER_CODES
            weather_cond = WMO_WEATHER_CODES.get(code, "Sunny")
        except Exception:
            pass
            
    recs = recommendation_engine.get_budget_recommendations(req.budget, req.city_name, req.country)
    checklist = recommendation_engine.generate_checklist(categories, weather_cond)
    
    recs["checklist"] = checklist
    return {"status": "success", "data": recs}

@router.post("/itinerary")
def create_itinerary(req: ItineraryRequest):
    itinerary = itinerary_service.generate_day_wise_itinerary(req.destination_id, req.days)
    return {"status": "success", "data": itinerary}
