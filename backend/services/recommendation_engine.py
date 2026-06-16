def get_budget_recommendations(budget: float, city_name: str, country: str):
    """
    Rule-based recommendation engine.
    Calculates package type, accommodation suggestions, transport, and highlights based on budget.
    """
    city_cap = city_name.capitalize()
    
    if budget < 10000:
        package_name = "Eco Budget Backpacking"
        tier = "Budget"
        suggested_stay = "Boutique Hostels & Homestays"
        transport = "Public Transit Pass & Walking Tours"
        activities = [
            f"Self-guided historic walk in downtown {city_cap}",
            "Visit free public parks and open-air markets",
            "Taste local street food specialties",
            "Explore municipal museums on free-entry days"
        ]
        avg_cost_breakdown = {
            "Accommodation": "40%",
            "Food & Dining": "30%",
            "Local Travel": "15%",
            "Activities": "15%"
        }
        description = f"Explore the local charm of {city_cap} without breaking the bank. This package focuses on cultural immersion, street food, and walking trails."
        
    elif budget < 50000:
        package_name = "Comfort Explorers Getaway"
        tier = "Comfort"
        suggested_stay = "3-Star Boutique Hotels or Premium Airbnbs"
        transport = "Rideshare Apps & Hop-on-Hop-off Tourist Bus"
        activities = [
            f"Guided walking tour of popular landmarks in {city_cap}",
            "Half-day culinary experience and local dining tour",
            "Admission ticket to top-rated historical sights",
            "Shopping at authentic local artisan workshops"
        ]
        avg_cost_breakdown = {
            "Accommodation": "45%",
            "Food & Dining": "25%",
            "Local Travel": "10%",
            "Activities": "20%"
        }
        description = f"The perfect balance of comfort and adventure. Enjoy premium stays, curated tours, and dine at highly-rated local restaurants in {city_cap}."
        
    else:
        package_name = "Premium Luxury Escape"
        tier = "Luxury"
        suggested_stay = "5-Star Resorts or Luxury Heritage Hotels"
        transport = "Private Chauffeur & VIP Airport Transfers"
        activities = [
            f"Private VIP guided tour of {city_cap}'s iconic landmarks",
            "Exclusive fine-dining tasting menu at Michelin-rated venues",
            "Full-day private yacht or premium excursion",
            "Luxury spa session and private wellness experience"
        ]
        avg_cost_breakdown = {
            "Accommodation": "50%",
            "Food & Dining": "20%",
            "Local Travel": "10%",
            "Activities": "20%"
        }
        description = f"Indulge in a premium travel experience. Every detail in {city_cap} is taken care of with private guides, luxury stays, and exclusive culinary access."
        
    return {
        "package_name": package_name,
        "tier": tier,
        "budget_limit": budget,
        "destination": f"{city_cap}, {country}",
        "suggested_stay": suggested_stay,
        "transport": transport,
        "activities": activities,
        "avg_cost_breakdown": avg_cost_breakdown,
        "description": description
    }

def generate_checklist(categories: list, weather_condition: str):
    """
    Rule-based travel checklist generator.
    Combines weather conditions and tourist place categories to build custom checklists.
    """
    checklist = [
        "Passport / National ID & Visa documents",
        "Mobile phone charger and universal travel adapter",
        "Personal toiletries & basic medicine kit",
        "Debit/Credit cards & small amount of local cash"
    ]
    
    # Weather-based rules
    weather_lower = weather_condition.lower()
    if "rain" in weather_lower:
        checklist.extend(["Travel umbrella", "Waterproof jacket/raincoat", "Waterproof footwear"])
    elif "sunny" in weather_lower or "hot" in weather_lower:
        checklist.extend(["UV Sunglasses", "Sunscreen (SPF 50+)", "Wide-brimmed sun hat", "Reusable water bottle"])
    elif "snow" in weather_lower or "cold" in weather_lower or "windy" in weather_lower:
        checklist.extend(["Thermal innerwear", "Warm fleece jacket or overcoat", "Beanie & gloves", "Lip balm & moisturizer"])
        
    # Category-based rules
    cats_lower = [c.lower() for c in categories]
    if "temple" in cats_lower or "historical" in cats_lower:
        checklist.append("Modest dress (shoulders and knees covered) for religious sites")
    if "adventure" in cats_lower or "hiking" in cats_lower:
        checklist.extend(["Sturdy hiking shoes", "Compact first-aid supplies", "Comfortable activewear"])
    if "beach" in cats_lower:
        checklist.extend(["Swimwear", "Quick-dry microfiber beach towel", "Waterproof dry-bag"])
    if "museum" in cats_lower:
        checklist.append("Comfortable walking sneakers (significant standing time)")
        
    return list(set(checklist)) # Deduplicate
