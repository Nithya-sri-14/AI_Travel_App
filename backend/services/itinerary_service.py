from backend.database import db_connection

def generate_day_wise_itinerary(destination_id: int, days: int = 3):
    """
    Generates a rule-based day-wise itinerary.
    Distributes tourist places based on categories and typical optimal visit times:
    - Morning: Historical & Temples
    - Afternoon: Museums (indoor)
    - Evening: Beaches, Parks & Adventures
    """
    # Fetch tourist places from DB using randomized query
    _, is_sqlite = db_connection.get_connection()
    random_func = "RANDOM()" if is_sqlite else "RAND()"
    places = db_connection.execute_read(
        f"SELECT * FROM tourist_places WHERE destination_id = %s ORDER BY {random_func}",
        (destination_id,)
    )
    
    if not places:
        return []
        
    # Categorize places
    morning_candidates = [p for p in places if p["category"] in ["Historical", "Temple"]]
    afternoon_candidates = [p for p in places if p["category"] in ["Museum"]]
    evening_candidates = [p for p in places if p["category"] in ["Beach", "Adventure"]]
    
    # Rest of the places can act as wildcards
    other_candidates = [p for p in places if p not in morning_candidates + afternoon_candidates + evening_candidates]
    
    itinerary = []
    
    for day in range(1, days + 1):
        day_schedule = {
            "day": day,
            "morning": None,
            "afternoon": None,
            "evening": None
        }
        
        # Morning assignment
        if morning_candidates:
            day_schedule["morning"] = morning_candidates.pop(0)
        elif other_candidates:
            day_schedule["morning"] = other_candidates.pop(0)
            
        # Afternoon assignment
        if afternoon_candidates:
            day_schedule["afternoon"] = afternoon_candidates.pop(0)
        elif other_candidates:
            day_schedule["afternoon"] = other_candidates.pop(0)
            
        # Evening assignment
        if evening_candidates:
            day_schedule["evening"] = evening_candidates.pop(0)
        elif other_candidates:
            day_schedule["evening"] = other_candidates.pop(0)
            
        # If still empty spots and candidates remain, fill them
        all_spots = ["morning", "afternoon", "evening"]
        for spot in all_spots:
            if not day_schedule[spot] and other_candidates:
                day_schedule[spot] = other_candidates.pop(0)
            elif not day_schedule[spot] and morning_candidates:
                day_schedule[spot] = morning_candidates.pop(0)
            elif not day_schedule[spot] and afternoon_candidates:
                day_schedule[spot] = afternoon_candidates.pop(0)
            elif not day_schedule[spot] and evening_candidates:
                day_schedule[spot] = evening_candidates.pop(0)
                
        # Only add days that have at least one activity
        if day_schedule["morning"] or day_schedule["afternoon"] or day_schedule["evening"]:
            itinerary.append(day_schedule)
            
    return itinerary
