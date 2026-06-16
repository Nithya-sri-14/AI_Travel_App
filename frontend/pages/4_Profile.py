import streamlit as st
import requests
import pandas as pd
import os

# Set page config
st.set_page_config(page_title="User Portal & Admin Governance", page_icon="👤", layout="wide")

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

st.title("👤 User Portal & System Governance")
st.write("Manage your profile, view booking credentials, or audit system logs if Admin.")

# Cancel Booking handler
def cancel_booking(booking_id):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        res = requests.delete(f"{backend_url}/api/bookings/{booking_id}", headers=headers, timeout=5)
        if res.status_code == 200:
            st.success("Booking cancelled successfully.")
        else:
            st.error(f"Error cancelling booking: {res.json().get('detail', 'Unauthorized')}")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")

# Check session state
if not st.session_state.user:
    tab1, tab2 = st.tabs(["🔒 Sign In", "📝 Create Account"])
    
    with tab1:
        st.subheader("Login to your Account")
        with st.form("login_form"):
            login_email = st.text_input("Email Address")
            login_password = st.text_input("Password", type="password")
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
                        
    with tab2:
        st.subheader("Register New Account")
        with st.form("register_form"):
            reg_name = st.text_input("Full Name")
            reg_email = st.text_input("Email Address")
            reg_phone = st.text_input("Phone Number")
            reg_password = st.text_input("Password", type="password")
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

else:
    # User is logged in
    user = st.session_state.user
    
    col_profile, col_actions = st.columns([1, 3])
    
    with col_profile:
        # User details card
        st.markdown(
            f"""
            <div class="stCard" style="text-align: center;">
                <h3 style="margin-top:0;">{user['name']}</h3>
                <p>🔑 <b>Role:</b> <span style="color:#ff8a00; font-weight:600;">{user['role']}</span></p>
                <p>👤 <b>ID:</b> {user['user_id']}</p>
                <p>📧 <b>Email:</b> {user['email']}</p>
                <p>📞 <b>Phone:</b> {user['phone'] or 'N/A'}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Sign Out", width="stretch"):
            st.session_state.user = None
            st.session_state.token = None
            st.rerun()
            
    with col_actions:
        # Determine views based on roles (Governance / RBAC)
        if user["role"] == "Admin":
            tab_bookings, tab_audit, tab_users = st.tabs(["✈️ My Bookings", "📜 Audit Trails (Governance)", "👥 Registered Users"])
        else:
            tab_bookings, = st.tabs(["✈️ My Bookings"])
            tab_audit = None
            tab_users = None
            
        with tab_bookings:
            st.subheader("My Flight Bookings")
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            try:
                res = requests.get(f"{backend_url}/api/bookings/user/{user['user_id']}", headers=headers, timeout=5)
                if res.status_code == 200:
                    bookings = res.json()["data"]
                    
                    if not bookings:
                        st.info("You don't have any bookings yet. Search flights on the 'Flights' page and book your tickets!")
                    else:
                        for b in bookings:
                            b_col1, b_col2, b_col3, b_col4 = st.columns([2, 3, 2, 1])
                            
                            with b_col1:
                                st.markdown(f"#### 🏢 {b['airline']}")
                                st.write(f"🎫 **Booking ID:** #{b['booking_id']}")
                                st.write(f"📅 **Booked:** {b['booking_date'][:16]}")
                                
                            with b_col2:
                                st.markdown(f"✈️ **Route:** {b['source_city']} ➡️ {b['destination_city']}")
                                st.write(f"🛫 **Departure:** {b['departure_time']}")
                                st.write(f"🛬 **Arrival:** {b['arrival_time']}")
                                
                            with b_col3:
                                st.markdown(f"### ₹{b['price']}")
                                st.markdown(f"🟢 **Status:** {b['status']}")
                                
                            with b_col4:
                                st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
                                st.button(
                                    "Cancel", 
                                    key=f"cancel_{b['booking_id']}",
                                    on_click=cancel_booking,
                                    args=(b['booking_id'],)
                                )
                            st.markdown("<hr style='margin:10px 0; opacity:0.3;'/>", unsafe_allow_html=True)
                else:
                    st.error("Error retrieving booking history.")
            except Exception as e:
                st.error(f"Error connecting to backend: {e}")
                
        if tab_audit:
            with tab_audit:
                st.subheader("📜 System Audit Trails")
                st.write("Real-time logging of sensitive actions, failed logins, and database queries for system governance.")
                
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                try:
                    audit_res = requests.get(f"{backend_url}/api/admin/audit-logs", headers=headers, timeout=5)
                    if audit_res.status_code == 200:
                        logs = audit_res.json()["data"]
                        
                        if not logs:
                            st.info("No audit logs recorded in the system yet.")
                        else:
                            # Render logs as a beautiful table
                            df_logs = pd.DataFrame(logs)
                            # Reorder columns for display
                            df_logs_display = df_logs[["timestamp", "action", "user_name", "ip_address", "status", "details"]]
                            df_logs_display.columns = ["Timestamp", "Action", "Performed By", "IP Address", "Status", "Details/Metadata"]
                            st.dataframe(df_logs_display, width="stretch", hide_index=True)
                    else:
                        st.error("Unauthorized to view audit trails.")
                except Exception as e:
                    st.error(f"Error fetching logs: {e}")
                    
        if tab_users:
            with tab_users:
                st.subheader("👥 System Registered Users")
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                try:
                    users_res = requests.get(f"{backend_url}/api/admin/users", headers=headers, timeout=5)
                    if users_res.status_code == 200:
                        all_users = users_res.json()["data"]
                        df_users = pd.DataFrame(all_users)
                        df_users.columns = ["User ID", "Full Name", "Email Address", "Phone Number", "Access Role"]
                        st.dataframe(df_users, width="stretch", hide_index=True)
                    else:
                        st.error("Unauthorized to view users directory.")
                except Exception as e:
                    st.error(f"Error fetching users: {e}")
