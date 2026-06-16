import unittest
from fastapi.testclient import TestClient
import os
import sys

# Ensure parent folder is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.database import db_connection
from backend import config

class TestSmartTravellerEnterpriseAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Force SQLite for unit tests and clean DB
        os.environ["DB_TYPE"] = "sqlite"
        db_connection.init_db()
        cls.client = TestClient(app)
        
        # Re-initialize database to ensure clean test state
        db_connection.execute_query("DELETE FROM bookings")
        db_connection.execute_query("DELETE FROM users")
        db_connection.execute_query("DELETE FROM destinations")
        db_connection.execute_query("DELETE FROM tourist_places")
        db_connection.execute_query("DELETE FROM audit_logs")

    def test_01_registration_and_login(self):
        # Register Admin (first user)
        res = self.client.post(
            "/api/users/register",
            json={"name": "Alice Admin", "email": "alice@admin.com", "phone": "123", "password": "password123"}
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()["role"], "Admin")
        self.admin_id = res.json()["user_id"]
        
        # Register standard User (second user)
        res2 = self.client.post(
            "/api/users/register",
            json={"name": "Bob User", "email": "bob@user.com", "phone": "456", "password": "password123"}
        )
        self.assertEqual(res2.status_code, 201)
        self.assertEqual(res2.json()["role"], "User")
        self.user_id = res2.json()["user_id"]
        
        # Login Admin to get token
        login_res = self.client.post(
            "/api/users/login",
            json={"email": "alice@admin.com", "password": "password123"}
        )
        self.assertEqual(login_res.status_code, 200)
        TestSmartTravellerEnterpriseAPI.admin_token = login_res.json()["access_token"]
        TestSmartTravellerEnterpriseAPI.admin_id = self.admin_id
        
        # Login User to get token
        login_res2 = self.client.post(
            "/api/users/login",
            json={"email": "bob@user.com", "password": "password123"}
        )
        self.assertEqual(login_res2.status_code, 200)
        TestSmartTravellerEnterpriseAPI.user_token = login_res2.json()["access_token"]
        TestSmartTravellerEnterpriseAPI.user_id = self.user_id

    def test_02_live_destination_search_exceptions(self):
        # Verify it succeeds with 200 OK due to keyless OpenStreetMap fallback geocoding
        response = self.client.get("/api/destinations/search?city=paris")
        self.assertEqual(response.status_code, 200)

    def test_03_rbac_protection(self):
        # Bob User tries to access Admin Audit Logs -> Should fail with 403 Forbidden
        headers = {"Authorization": f"Bearer {self.user_token}"}
        audit_res = self.client.get("/api/admin/audit-logs", headers=headers)
        self.assertEqual(audit_res.status_code, 403)
        
        # Admin gets full user directory
        admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        users_res = self.client.get("/api/admin/users", headers=admin_headers)
        self.assertEqual(users_res.status_code, 200)
        self.assertTrue(len(users_res.json()["data"]) >= 2)

    def test_04_live_flight_search_exceptions(self):
        # With default/configured credentials, it should return 200 OK using either live APIs or Simulated fallback
        response = self.client.get("/api/flights/search?source=mumbai&destination=paris&date=2026-06-20")
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.json()["provider"], ["High-Fidelity Flight Simulator", "Aviationstack API"])
        self.assertEqual(len(response.json()["data"]), 5)

    def test_05_rate_limiting(self):
        # Send 12 fast requests to search destination -> should trigger 429
        # The limit category is 'search', which is 10/min. This triggers before the API key check!
        limited_triggered = False
        for i in range(15):
            res = self.client.get("/api/destinations/search?city=london")
            if res.status_code == 429:
                limited_triggered = True
                break
        self.assertTrue(limited_triggered)

    def test_06_flight_api_providers(self):
        # Override config.FLIGHT_PROVIDER to simulated
        old_provider = config.FLIGHT_PROVIDER
        config.FLIGHT_PROVIDER = "simulated"
        try:
            response = self.client.get("/api/flights/search?source=mumbai&destination=paris&date=2026-06-20")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["provider"], "High-Fidelity Flight Simulator")
            flights = data["data"]
            self.assertEqual(len(flights), 5)
            for f in flights:
                self.assertIn("airline", f)
                self.assertIn("departure_time", f)
                self.assertIn("arrival_time", f)
                self.assertTrue(f["price"] > 0)
                # Confirm it's using realistic airline names
                self.assertTrue(any(carrier in f["airline"] for carrier in ["Air India", "Emirates", "Air France", "Qatar Airways", "Vistara", "Etihad Airways"]))
        finally:
            config.FLIGHT_PROVIDER = old_provider

if __name__ == "__main__":
    unittest.main()
