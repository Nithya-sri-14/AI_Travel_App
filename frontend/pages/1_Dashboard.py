import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import os

# Set page config
st.set_page_config(page_title="Dashboard & Analytics", page_icon="📊", layout="wide")

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

st.title("📊 Platform Dashboard & Analytics")
st.write("Real-time travel metrics, analytics charts, and trend data.")

backend_url = st.session_state.get("backend_url", "http://localhost:8000")

# Fetch Stats from Backend
@st.cache_data(ttl=10) # Cache for 10 seconds
def fetch_stats():
    try:
        res = requests.get(f"{backend_url}/api/stats", timeout=3)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Could not connect to FastAPI backend at {backend_url}. Make sure your backend server is running!")
    return None

stats = fetch_stats()

if stats:
    # KPI Grid
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">👤 Total Users</div>
                <div class="metric-value">{stats['total_users']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col2:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">🗺️ Destinations Cached</div>
                <div class="metric-value">{stats['total_destinations']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col3:
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-label">✈️ Total Bookings</div>
                <div class="metric-value">{stats['total_bookings']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col4:
        st.markdown(
            f"""
            <div class="metric-container" style="background: linear-gradient(135deg, #f857a6 0%, #ff5858 100%);">
                <div class="metric-label">🔥 Hot Destination</div>
                <div class="metric-value" style="font-size: 1.25rem; padding: 6px 0;">{stats['popular_destination']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.write("---")
    
    # Charts Row
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("🏛️ Attractions by Category")
        cat_dist = stats.get("category_distribution", [])
        
        if cat_dist:
            df_cat = pd.DataFrame(cat_dist)
            fig_pie = px.pie(
                df_cat, 
                values="count", 
                names="category", 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350)
            st.plotly_chart(fig_pie, width="stretch")
        else:
            st.info("No tourist places data available yet. Go to 'Destinations' page to search cities and populate attractions.")
            
    with chart_col2:
        st.subheader("📈 Popular Destination Booking Trends")
        trends = stats.get("booking_trends", [])
        
        if trends:
            df_trends = pd.DataFrame(trends)
            fig_bar = px.bar(
                df_trends,
                x="city_name",
                y="booking_count",
                labels={"city_name": "City", "booking_count": "Total Bookings"},
                color="booking_count",
                color_continuous_scale="Viridis"
            )
            fig_bar.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350)
            st.plotly_chart(fig_bar, width="stretch")
        else:
            st.info("No bookings registered yet. Try booking flights in the 'Flights' tab to see data populate here!")
else:
    st.warning("Please start the FastAPI backend server first.")
