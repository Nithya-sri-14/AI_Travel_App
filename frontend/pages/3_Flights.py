import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import os

# Set page config
st.set_page_config(page_title="Flight Search & Bookings", page_icon="✈️", layout="wide")

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

# Try to resolve backend URL from session state, secrets, environment variables, or local fallback
backend_url = st.session_state.get("backend_url")
if not backend_url:
    try:
        backend_url = st.secrets.get("BACKEND_URL", os.environ.get("BACKEND_URL", "http://localhost:8000"))
    except Exception:
        backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
    st.session_state.backend_url = backend_url

st.title("✈️ Flight Search & Comparison Module")
st.write("Compare flight availability, airline pricing, and confirm your bookings.")

# Search Criteria
with st.form("flight_search_form"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        source_city = st.text_input("Source City", placeholder="e.g. Mumbai, New York")
    with col2:
        dest_city = st.text_input("Destination City", placeholder="e.g. London, Paris")
    with col3:
        tomorrow = datetime.now() + timedelta(days=1)
        travel_date = st.date_input("Travel Date", value=tomorrow, min_value=datetime.now())
        
    search_submitted = st.form_submit_button("Search Flights", width="stretch")

def book_flight(flight_id, airline, price):
    if not st.session_state.user or not st.session_state.token:
        st.warning("⚠️ You must be logged in to book a flight. Please go to the User Portal page to log in or register.")
        return
        
    user_id = st.session_state.user["user_id"]
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        res = requests.post(
            f"{backend_url}/api/bookings",
            json={"user_id": user_id, "flight_id": flight_id},
            headers=headers,
            timeout=5
        )
        if res.status_code == 201:
            st.balloons()
            st.success(f"🎉 Booking Confirmed! Flight on **{airline}** for **₹{price:.2f}** has been secured. Check your profile for tickets.")
        else:
            st.error(f"Could not complete the booking: {res.json().get('detail', 'Unauthorized')}")
    except Exception as e:
        st.error(f"Error executing booking: {e}")

if search_submitted:
    if not source_city or not dest_city:
        st.error("Please fill in both Source and Destination cities.")
    else:
        st.write("---")
        st.subheader(f"✈️ Flights from {source_city.capitalize()} to {dest_city.capitalize()} on {travel_date}")
        
        with st.spinner("Searching for available routes..."):
            try:
                date_str = travel_date.strftime("%Y-%m-%d")
                res = requests.get(
                    f"{backend_url}/api/flights/search",
                    params={"source": source_city, "destination": dest_city, "date": date_str},
                    timeout=10
                )
                
                # Handle API Key missing notifications (503 Service Unavailable)
                if res.status_code == 503:
                    st.error(
                        f"⚠️ **Duffel API Access Token Missing:**\n\n{res.json().get('detail')}\n\n"
                        "Please configure your Duffel Token in `backend/.env`:\n"
                        "```env\nDUFFEL_ACCESS_TOKEN=your_duffel_access_token_here\n```"
                    )
                elif res.status_code == 200:
                    res_json = res.json()
                    flights = res_json.get("data", [])
                    provider = res_json.get("provider", "Live API")
                    
                    st.info(f"📡 **Flight Data Source:** Results resolved via **{provider}**")
                    
                    if not flights:
                        st.info("No flights found matching the criteria.")
                    else:
                        # Convert to DataFrame for a quick tabular summary
                        df_display = pd.DataFrame(flights)
                        df_display = df_display[["airline", "departure_time", "arrival_time", "price"]]
                        df_display.columns = ["Airline", "Departure", "Arrival", "Price (INR)"]
                        
                        # Show as table first
                        st.dataframe(df_display, width="stretch", hide_index=True)
                        
                        st.write("### 🎫 Select a flight to Book:")
                        # Render beautiful cards for selection
                        for flight in flights:
                            col_f1, col_f2, col_f3, col_f4 = st.columns([1, 2, 1, 1])
                            
                            with col_f1:
                                st.markdown(f"#### 🏢 {flight['airline']}")
                            with col_f2:
                                st.markdown(
                                    f"""
                                    <div style='font-size:0.9rem;'>
                                        🛫 <b>Departure:</b> {flight['departure_time']}<br/>
                                        🛬 <b>Arrival:</b> {flight['arrival_time']}
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                            with col_f3:
                                st.markdown(f"### ₹{flight['price']:.2f}")
                            with col_f4:
                                st.button(
                                    f"Book Now", 
                                    key=f"btn_{flight['flight_id']}",
                                    on_click=book_flight,
                                    args=(flight['flight_id'], flight['airline'], flight['price'])
                                )
                            st.markdown("<hr style='margin: 8px 0; opacity: 0.3;'/>", unsafe_allow_html=True)
                else:
                    st.error(f"Failed to fetch flights: {res.json().get('detail', 'Unknown error')}")
            except Exception as e:
                st.error(f"Error connecting to backend: {e}")
