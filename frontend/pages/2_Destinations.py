import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
import os

# Set page config
st.set_page_config(page_title="Destination Explorer", page_icon="🗺️", layout="wide")

# Helper to load CSS
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Session State Initialization & Lock Check
if "user" not in st.session_state:
    st.session_state.user = None
if "token" not in st.session_state:
    st.session_state.token = None

if not st.session_state.user:
    st.warning("🔒 **Access Locked:** Please log in first on the Home page to access this page.")
    st.page_link("app.py", label="Go to Home / Login Page", icon="🔑")
    st.stop()

backend_url = st.session_state.get("backend_url", "http://localhost:8000")

st.title("🗺️ Destination Explorer & Weather Intelligence")
st.write("Search destinations, check live weather, view interactive maps, build itineraries, and get recommendation packages.")

# Search form
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        city_input = st.text_input("Enter Destination City", placeholder="e.g. Paris, London, Tokyo, Mumbai, Sydney")
    with col2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        search_btn = st.button("Explore Destination", width="stretch")

if search_btn and city_input:
    # Fetch Destination details
    with st.spinner(f"Exploring {city_input.capitalize()}..."):
        try:
            dest_res = requests.get(f"{backend_url}/api/destinations/search", params={"city": city_input}, timeout=10)
            weather_res = requests.get(f"{backend_url}/api/weather", params={"city": city_input}, timeout=10)
            
            # Reset previous searches first
            if "current_destination" in st.session_state:
                del st.session_state["current_destination"]
            if "current_weather" in st.session_state:
                del st.session_state["current_weather"]
            if "search_city" in st.session_state:
                del st.session_state["search_city"]
                
            # Handle API Key missing notifications (503 Service Unavailable)
            if dest_res.status_code == 503:
                st.error(
                    f"⚠️ **Google Places API Key Missing:**\n\n{dest_res.json().get('detail')}\n\n"
                    "Please create a `.env` file in the `backend/` directory and configure your Google Places API Key:\n"
                    "```env\nGOOGLE_PLACES_API_KEY=your_key_here\n```"
                )
            elif weather_res.status_code == 503:
                st.error(
                    f"⚠️ **OpenWeatherMap API Key Missing:**\n\n{weather_res.json().get('detail')}\n\n"
                    "Please configure your OpenWeatherMap key in `backend/.env`:\n"
                    "```env\nOPENWEATHER_API_KEY=your_key_here\n```"
                )
            elif dest_res.status_code == 200 and weather_res.status_code == 200:
                dest_data = dest_res.json()["data"]
                weather_data = weather_res.json()["data"]
                
                # Setup details
                st.session_state.current_destination = dest_data
                st.session_state.current_weather = weather_data
                st.session_state.search_city = city_input
            else:
                # Handle general API errors
                if dest_res.status_code != 200:
                    st.error(f"Failed to fetch destination attractions: {dest_res.json().get('detail', 'Unknown Error')}")
                if weather_res.status_code != 200:
                    st.error(f"Failed to fetch weather forecast: {weather_res.json().get('detail', 'Unknown Error')}")
                    
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")

if "current_destination" in st.session_state and st.session_state.get("search_city"):
    dest = st.session_state.current_destination
    weather = st.session_state.current_weather
    
    st.write("---")
    
    # Header Details
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown(f"<h2 style='margin-bottom:0;'>Explore {dest['city_name']}, {dest['country']}</h2>", unsafe_allow_html=True)
        st.write(f"⭐ Rating: **{dest['rating']} / 5.0**")
        st.write(dest['description'])
    with header_col2:
        # Mini current weather panel
        st.markdown(
            f"""
            <div class="metric-container" style="background: linear-gradient(135deg, #2b5876 0%, #4e4376 100%); margin-bottom: 0;">
                <div class="metric-label">CURRENT WEATHER</div>
                <div class="metric-value">{weather['temperature']}°C</div>
                <div style="font-size: 0.95rem; font-weight: 500;">{weather['condition']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    tab1, tab2, tab3, tab4 = st.tabs(["🏛️ Attractions & Map", "🌦️ Weather Forecast", "📅 Itinerary Planner", "💰 Budget Recommender"])
    
    with tab1:
        map_col, list_col = st.columns([3, 2])
        
        with list_col:
            st.subheader("📍 Tourist Attractions")
            places_df = pd.DataFrame(dest["places"])
            if not places_df.empty:
                for idx, row in places_df.iterrows():
                    st.markdown(
                        f"""
                        <div class="stCard">
                            <h4 style='margin:0; color:#4776e6;'>{row['place_name']}</h4>
                            <p style='margin:2px 0; font-size:0.9rem;'>🏷️ <b>Category:</b> {row['category']} | ⭐ <b>Rating:</b> {row['rating']}</p>
                            <p style='margin:0; font-size:0.85rem; color:#666;'>📍 {row['address']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.info("No places returned.")
                
        with map_col:
            st.subheader("🗺️ Interactive Map")
            
            # Center map around first attraction's coordinates
            if dest["places"]:
                center_lat = dest["places"][0]["latitude"]
                center_lon = dest["places"][0]["longitude"]
            else:
                center_lat, center_lon = 0.0, 0.0
                
            m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
            
            # Add markers
            for place in dest["places"]:
                # Custom popup styling
                popup_html = f"""
                    <div style="font-family: 'Outfit', sans-serif; min-width: 150px;">
                        <h4 style="margin:0 0 5px 0; color:#4776e6;">{place['place_name']}</h4>
                        <b>Category:</b> {place['category']}<br/>
                        <b>Rating:</b> ⭐ {place['rating']}<br/>
                        <p style="margin:5px 0 0 0; font-size:0.8rem; color:#555;">{place['address']}</p>
                    </div>
                """
                iframe = folium.IFrame(html=popup_html, width=220, height=130)
                popup = folium.Popup(iframe, max_width=250)
                
                # Color code based on category
                color_map = {
                    "Historical": "red",
                    "Museum": "blue",
                    "Temple": "purple",
                    "Beach": "orange",
                    "Adventure": "green"
                }
                marker_color = color_map.get(place["category"], "gray")
                
                folium.Marker(
                    location=[place["latitude"], place["longitude"]],
                    popup=popup,
                    tooltip=place["place_name"],
                    icon=folium.Icon(color=marker_color, icon="info-sign")
                ).add_to(m)
                
            # Render Folium map in Streamlit
            st_folium(m, width=700, height=500, key="dest_map")
            
    with tab2:
        st.subheader("🌦️ 5-Day Weather Intelligence Forecast")
        
        # Grid layout for current metrics
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("Humidity", f"{weather['humidity']}%")
        with metric_col2:
            st.metric("Wind Speed", f"{weather['wind_speed']} m/s")
        with metric_col3:
            st.metric("Rain Probability", f"{weather['rain_probability']}%")
            
        st.write("#### Daily Forecast")
        fc_cols = st.columns(5)
        for idx, day in enumerate(weather["forecast"]):
            with fc_cols[idx]:
                # Visual weather card
                emoji_map = {
                    "Sunny": "☀️",
                    "Partly Cloudy": "⛅",
                    "Cloudy": "☁️",
                    "Light Rain": "🌧️",
                    "Windy": "💨",
                    "Rain": "🌧️",
                    "Clouds": "☁️",
                    "Clear": "☀️"
                }
                emoji = emoji_map.get(day["condition"], "☀️")
                st.markdown(
                    f"""
                    <div style='background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 15px; text-align: center;'>
                        <div style='font-size: 0.85rem; color: #888;'>{day['date']}</div>
                        <div style='font-size: 2.5rem; margin: 10px 0;'>{emoji}</div>
                        <div style='font-size: 1.5rem; font-weight: bold;'>{day['temp']}°C</div>
                        <div style='font-size: 0.9rem;'>{day['condition']}</div>
                        <div style='font-size: 0.8rem; color: #4776e6; margin-top: 5px;'>💧 {day['rain_prob']}% Rain</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
    with tab3:
        st.subheader("📅 Day-Wise Optimal Itinerary")
        days = st.slider("Select Duration (Days)", min_value=1, max_value=5, value=3)
        
        if st.button("Generate Smart Itinerary"):
            try:
                it_res = requests.post(
                    f"{backend_url}/api/destinations/itinerary",
                    json={"destination_id": dest["destination_id"], "days": days},
                    timeout=5
                )
                if it_res.status_code == 200:
                    it_data = it_res.json()["data"]
                    
                    if not it_data:
                        st.info("No tourist places registered to create an itinerary.")
                    else:
                        for day_plan in it_data:
                            st.markdown(f"### 🗓️ Day {day_plan['day']}")
                            
                            day_cols = st.columns(3)
                            slots = ["morning", "afternoon", "evening"]
                            slot_titles = ["🌅 Morning Activity", "☀️ Afternoon Activity", "🌙 Evening Activity"]
                            
                            for s_idx, slot in enumerate(slots):
                                with day_cols[s_idx]:
                                    place = day_plan[slot]
                                    if place:
                                        st.markdown(
                                            f"""
                                            <div style='background: rgba(255,255,255,0.04); border-left: 4px solid #8e54e9; padding: 12px; border-radius: 0 8px 8px 0; min-height: 120px;'>
                                                <h5 style='margin:0; color:#8e54e9;'>{slot_titles[s_idx]}</h5>
                                                <strong style='font-size: 1rem; display:block; margin-top:4px;'>{place['place_name']}</strong>
                                                <span style='font-size: 0.85rem; color:#888;'>🏷️ {place['category']} | ⭐ {place['rating']}</span>
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )
                                    else:
                                        st.markdown(
                                            f"""
                                            <div style='background: rgba(255,255,255,0.02); border-left: 4px solid #555; padding: 12px; border-radius: 0 8px 8px 0; min-height: 120px;'>
                                                <h5 style='margin:0; color:#555;'>{slot_titles[s_idx]}</h5>
                                                <span style='font-size: 0.9rem; color:#666; display:block; margin-top:10px;'>Relaxation or Shopping</span>
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )
                            st.write("")
                else:
                    st.error("Error generating itinerary.")
            except Exception as e:
                st.error(f"Failed to fetch itinerary: {e}")
                
    with tab4:
        st.subheader("💰 Smart Recommendations & Travel Checklist")
        budget = st.number_input("Enter Budget (INR)", min_value=1000, value=25000, step=5000)
        
        if st.button("Generate Recommendations"):
            try:
                rec_res = requests.post(
                    f"{backend_url}/api/destinations/recommendations",
                    json={"budget": budget, "city_name": dest["city_name"], "country": dest["country"]},
                    timeout=5
                )
                if rec_res.status_code == 200:
                    rec_data = rec_res.json()["data"]
                    
                    rec_col, list_col = st.columns(2)
                    
                    with rec_col:
                        st.markdown(
                            f"""
                            <div class="stCard">
                                <h3 style='margin:0 0 10px 0; color:#ff8a00;'>🏷️ {rec_data['package_name']}</h3>
                                <p style='font-size: 1.1rem; font-weight: 500;'>Tier: <b>{rec_data['tier']} Package</b></p>
                                <p>{rec_data['description']}</p>
                                <p>🏨 <b>Accommodation:</b> {rec_data['suggested_stay']}</p>
                                <p>🚗 <b>Local Transport:</b> {rec_data['transport']}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        st.markdown("##### 💸 Average Budget Distribution")
                        df_cost = pd.DataFrame([
                            {"Expense": k, "Percentage": float(v.replace("%", ""))}
                            for k, v in rec_data["avg_cost_breakdown"].items()
                        ])
                        st.dataframe(df_cost, width="stretch", hide_index=True)
                        
                    with list_col:
                        st.markdown("#### 🎒 Smart Travel Checklist")
                        st.write("Generated dynamically based on destination categories and current weather:")
                        for item in rec_data["checklist"]:
                            st.write(f"- [ ] {item}")
                else:
                    st.error("Error generating recommendations.")
            except Exception as e:
                st.error(f"Failed to fetch recommendations: {e}")
else:
    st.info("Search for a destination above to begin planning.")
