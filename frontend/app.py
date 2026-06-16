import streamlit as st
import os
import requests

# Set page config first
st.set_page_config(
    page_title="Smart Traveller App",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper to load CSS
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Session State Initialization
if "user" not in st.session_state:
    st.session_state.user = None
if "token" not in st.session_state:
    st.session_state.token = None
if "backend_url" not in st.session_state:
    # Check st.secrets first (wrapped in try/except to prevent StreamlitSecretNotFoundError when running locally)
    try:
        st.session_state.backend_url = st.secrets.get("BACKEND_URL", os.environ.get("BACKEND_URL", "http://localhost:8000"))
    except Exception:
        st.session_state.backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")

backend_url = st.session_state.backend_url

# Case 1: User is NOT logged in - Render Login/Register Screen & Hide Sidebar Nav
if not st.session_state.user:
    # Inject CSS to hide sidebar navigation until logged in
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("<h1 class='gradient-text' style='text-align: center; font-size: 3rem; margin-bottom: 5px;'>✈️ Smart Traveller Platform</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.25rem; color: #888; margin-bottom: 25px;'>Your Enterprise-ready Travel Intelligence & Planning Assistant</p>", unsafe_allow_html=True)
    
    st.write("---")
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("### 🗺️ Explore the Travel Intelligence Portal")
        st.write(
            "Welcome to the next generation of travel management. This system integrates strictly "
            "with live real-time API connectors and local fallback data registries to deliver a robust, "
            "always-available travel dashboard."
        )
        
        st.markdown(
            """
            <div class="stCard">
                <h4 style="margin-top: 0; color: #4776e6;">🔒 System Capabilities unlocked after Login:</h4>
                <p style="margin: 6px 0;">📊 <b>Dashboard:</b> Real-time statistics, trends, and tourist attractions metrics.</p>
                <p style="margin: 6px 0;">🗺️ <b>Destination Explorer:</b> Verified coordinates mapping, 5-day weather, and smart daily itineraries.</p>
                <p style="margin: 6px 0;">✈️ <b>Flights search:</b> Live <b>Duffel API</b> offers comparator and reservations booking.</p>
                <p style="margin: 6px 0;">📜 <b>Governance:</b> User profiles, personal bookings record, and admin system audit trails.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.info(
            "💡 **Enterprise Security:** All credentials and logins are signed via secure, time-restricted JWT tokens "
            "with passwords salted and hashed using Bcrypt. Enforced rate limits apply to prevent API abuse."
        )
        
    with col2:
        tab_login, tab_register = st.tabs(["🔒 Sign In", "📝 Create Account"])
        
        with tab_login:
            st.subheader("Login to your Account")
            with st.form("login_form"):
                login_email = st.text_input("Email Address", placeholder="e.g. alice@admin.com")
                login_password = st.text_input("Password", type="password", placeholder="Enter your password")
                login_submitted = st.form_submit_button("Sign In", width="stretch")
                
                if login_submitted:
                    if not login_email or not login_password:
                        st.error("Please fill in all fields.")
                    else:
                        try:
                            res = requests.post(
                                f"{backend_url}/api/users/login",
                                json={"email": login_email, "password": login_password},
                                timeout=5
                            )
                            if res.status_code == 200:
                                data = res.json()
                                st.session_state.token = data["access_token"]
                                st.session_state.user = data["user"]
                                st.success(f"Welcome back, {st.session_state.user['name']}!")
                                st.rerun()
                            else:
                                st.error(f"Login failed: {res.json().get('detail', 'Invalid credentials')}")
                        except Exception as e:
                            st.error(f"Error connecting to backend: {e}")
                            
        with tab_register:
            st.subheader("Register New Account")
            with st.form("register_form"):
                reg_name = st.text_input("Full Name", placeholder="e.g. Bob Smith")
                reg_email = st.text_input("Email Address", placeholder="e.g. bob@example.com")
                reg_phone = st.text_input("Phone Number", placeholder="e.g. +91 9999999999")
                reg_password = st.text_input("Password", type="password", placeholder="Choose a secure password")
                reg_submitted = st.form_submit_button("Register Account", width="stretch")
                
                if reg_submitted:
                    if not reg_name or not reg_email or not reg_password:
                        st.error("Name, email, and password are required.")
                    else:
                        try:
                            res = requests.post(
                                f"{backend_url}/api/users/register",
                                json={"name": reg_name, "email": reg_email, "phone": reg_phone, "password": reg_password},
                                timeout=5
                            )
                            if res.status_code == 201:
                                st.success("Account created successfully! Please sign in in the Sign In tab.")
                            else:
                                st.error(f"Registration failed: {res.json().get('detail', 'Error')}")
                        except Exception as e:
                            st.error(f"Error connecting to backend: {e}")

# Case 2: User is successfully logged in - Render post-auth welcome screen
else:
    user = st.session_state.user
    
    st.markdown(f"<h1 class='gradient-text'>✈️ Welcome, {user['name']}!</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.2rem; color: #888;'>Your session is active. You can now access all portal modules in the sidebar navigation.</p>", unsafe_allow_html=True)
    
    st.write("---")
    
    col_dash, col_actions = st.columns([1, 2], gap="large")
    
    with col_dash:
        # Profile details card
        st.markdown(
            f"""
            <div class="stCard">
                <h3 style="margin-top: 0; color: #4776e6;">👤 Active Session</h3>
                <p>🟢 <b>Name:</b> {user['name']}</p>
                <p>🔑 <b>Access Role:</b> <span style="color:#ff8a00; font-weight:600;">{user['role']}</span></p>
                <p>📧 <b>Email:</b> {user['email']}</p>
                <p>📞 <b>Phone:</b> {user['phone'] or 'N/A'}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if st.button("Logout Session", width="stretch"):
            st.session_state.user = None
            st.session_state.token = None
            st.rerun()
            
    with col_actions:
        st.markdown("### 🚀 Quick Navigation Links")
        st.write("Click on any of the core travel modules below to get started:")
        
        col_lnk1, col_lnk2 = st.columns(2)
        with col_lnk1:
            st.markdown(
                """
                <div style="padding: 15px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; min-height: 140px; margin-bottom: 15px;">
                    <h4 style="margin-top:0;">📊 Dashboard & Analytics</h4>
                    <p style="font-size:0.85rem; color:#888;">Analyze platform usage, hot destination trends, and tourist place categories.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.page_link("pages/1_Dashboard.py", label="Open Platform Dashboard", icon="📊")
            
            st.markdown(
                """
                <div style="padding: 15px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; min-height: 140px; margin-bottom: 15px; margin-top: 25px;">
                    <h4 style="margin-top:0;">✈️ Flight Booking Hub</h4>
                    <p style="font-size:0.85rem; color:#888;">Search routes, compare prices directly on Duffel, and make live test bookings.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.page_link("pages/3_Flights.py", label="Open Flight Search", icon="✈️")
            
        with col_lnk2:
            st.markdown(
                """
                <div style="padding: 15px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; min-height: 140px; margin-bottom: 15px;">
                    <h4 style="margin-top:0;">🗺️ Destinations Explorer</h4>
                    <p style="font-size:0.85rem; color:#888;">View interactive maps, check forecasts, and generate day-wise itineraries.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.page_link("pages/2_Destinations.py", label="Open Destination Explorer", icon="🗺️")
            
            st.markdown(
                """
                <div style="padding: 15px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; min-height: 140px; margin-bottom: 15px; margin-top: 25px;">
                    <h4 style="margin-top:0;">👤 Account & Governance</h4>
                    <p style="font-size:0.85rem; color:#888;">Cancel active bookings, view tickets, and review audit trail logs (Admin only).</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.page_link("pages/4_Profile.py", label="Open Account Portal", icon="👤")

st.write("---")
st.markdown("<p style='text-align: center; color: #555; font-size: 0.8rem;'>Smart Traveller Application &copy; 2026. Made with Streamlit & FastAPI.</p>", unsafe_allow_html=True)
