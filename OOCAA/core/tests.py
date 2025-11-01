from django.test import TestCase

# Create your tests here.

"""
Test script for OOCAA API
Run this script to test the API endpoints after starting the server
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api"
USERNAME = "testuser"
PASSWORD = "testpass123"
EMAIL = "test@example.com"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_response(response):
    """Print formatted response"""
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def test_registration():
    """Test user registration"""
    print_section("Testing User Registration")
    
    data = {
        "username": USERNAME,
        "email": EMAIL,
        "password": PASSWORD,
        "password_confirm": PASSWORD,
        "role": "analyst",
        "organization": "Test Organization"
    }
    
    response = requests.post(f"{BASE_URL}/register/", json=data)
    print_response(response)
    
    if response.status_code == 201:
        return response.json().get('token')
    return None

def test_login():
    """Test user login"""
    print_section("Testing User Login")
    
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/login/", json=data)
    print_response(response)
    
    if response.status_code == 200:
        return response.json().get('token')
    return None

def test_profile(token):
    """Test getting user profile"""
    print_section("Testing User Profile")
    
    headers = {"Authorization": f"Token {token}"}
    response = requests.get(f"{BASE_URL}/profile/", headers=headers)
    print_response(response)

def test_create_cdm(token):
    """Test creating a CDM"""
    print_section("Testing CDM Creation")
    
    headers = {"Authorization": f"Token {token}"}
    tca = datetime.now() + timedelta(days=4)
    
    data = {
        "cdm_id": "CDM_TEST_001",
        "creation_date": datetime.now().isoformat() + "Z",
        "originator": "NASA",
        "message_for": "SATELLITE-OPERATOR",
        "message_id": "MSG_TEST_001",
        "object1_name": "TEST-SATELLITE-A",
        "object1_designator": "2024-001A",
        "object1_catalog_name": "SATCAT",
        "object1_object_type": "PAYLOAD",
        "object2_name": "TEST-DEBRIS-123",
        "object2_designator": "1999-025BZ",
        "object2_catalog_name": "SATCAT",
        "object2_object_type": "DEBRIS",
        "tca": tca.isoformat() + "Z",
        "miss_distance": 500.5,
        "relative_speed": 14500.0,
        "collision_probability": 0.00015,
        "collision_probability_method": "Foster-1992",
        "object1_position": [7000.0, 0.0, 0.0],
        "object1_velocity": [0.0, 7.5, 0.0],
        "object2_position": [7000.5, 0.0, 0.0],
        "object2_velocity": [0.0, -7.0, 0.0],
        "risk_level": "high",
        "status": "received",
        "notes": "Test CDM for API validation"
    }
    
    response = requests.post(f"{BASE_URL}/cdms/", json=data, headers=headers)
    print_response(response)
    
    if response.status_code == 201:
        return response.json().get('id')
    return None

def test_list_cdms(token):
    """Test listing CDMs"""
    print_section("Testing CDM List")
    
    headers = {"Authorization": f"Token {token}"}
    response = requests.get(f"{BASE_URL}/cdms/", headers=headers)
    print_response(response)

def test_get_cdm(token, cdm_id):
    """Test getting a specific CDM"""
    print_section(f"Testing Get CDM (ID: {cdm_id})")
    
    if not cdm_id:
        print("Skipping - no CDM ID available")
        return
    
    headers = {"Authorization": f"Token {token}"}
    response = requests.get(f"{BASE_URL}/cdms/{cdm_id}/", headers=headers)
    print_response(response)

def test_high_risk_cdms(token):
    """Test getting high risk CDMs"""
    print_section("Testing High Risk CDMs")
    
    headers = {"Authorization": f"Token {token}"}
    response = requests.get(f"{BASE_URL}/cdms/high_risk/", headers=headers)
    print_response(response)

def test_create_maneuver(token, cdm_id):
    """Test creating a maneuver plan"""
    print_section("Testing Maneuver Plan Creation")
    
    if not cdm_id:
        print("Skipping - no CDM ID available")
        return None
    
    headers = {"Authorization": f"Token {token}"}
    maneuver_time = datetime.now() + timedelta(days=2)
    
    data = {
        "cdm": cdm_id,
        "maneuver_id": "MAN_TEST_001",
        "maneuver_type": "in_track",
        "delta_v": [0.5, 0.0, 0.0],
        "maneuver_time": maneuver_time.isoformat() + "Z",
        "execution_duration": 300.0,
        "new_miss_distance": 5000.0,
        "new_collision_probability": 0.000001,
        "fuel_cost": 2.5,
        "status": "proposed",
        "notes": "Test maneuver plan"
    }
    
    response = requests.post(f"{BASE_URL}/maneuvers/", json=data, headers=headers)
    print_response(response)
    
    if response.status_code == 201:
        return response.json().get('id')
    return None

def test_collision_analysis(token):
    """Test collision analysis"""
    print_section("Testing Collision Analysis")
    
    headers = {"Authorization": f"Token {token}"}
    
    data = {
        "cdm_ids": ["CDM_TEST_001"],
        "analysis_method": "Combined Probability Analysis",
        "time_window_start": datetime.now().isoformat() + "Z",
        "time_window_end": (datetime.now() + timedelta(days=10)).isoformat() + "Z"
    }
    
    response = requests.post(f"{BASE_URL}/analyses/analyze_collision/", json=data, headers=headers)
    print_response(response)

def test_dashboard_stats(token):
    """Test dashboard statistics"""
    print_section("Testing Dashboard Statistics")
    
    headers = {"Authorization": f"Token {token}"}
    response = requests.get(f"{BASE_URL}/dashboard/stats/", headers=headers)
    print_response(response)

def test_logout(token):
    """Test user logout"""
    print_section("Testing User Logout")
    
    headers = {"Authorization": f"Token {token}"}
    response = requests.post(f"{BASE_URL}/logout/", headers=headers)
    print_response(response)

def main():
    """Run all tests"""
    print("\n" + "🚀"*30)
    print("  OOCAA API Test Suite")
    print("🚀"*30)
    print(f"\nBase URL: {BASE_URL}")
    print("Make sure the server is running: python manage.py runserver")
    input("\nPress Enter to start testing...")
    
    # Register and get token (or login if already registered)
    token = test_registration()
    if not token:
        token = test_login()
    
    if not token:
        print("\n❌ Failed to get authentication token. Exiting.")
        return
    
    print(f"\n✅ Authentication successful! Token: {token[:20]}...")
    
    # Test user profile
    test_profile(token)
    
    # Test CDM operations
    cdm_id = test_create_cdm(token)
    test_list_cdms(token)
    test_get_cdm(token, cdm_id)
    test_high_risk_cdms(token)
    
    # Test maneuver operations
    maneuver_id = test_create_maneuver(token, cdm_id)
    
    # Test collision analysis
    test_collision_analysis(token)
    
    # Test dashboard
    test_dashboard_stats(token)
    
    # Test logout
    test_logout(token)
    
    print("\n" + "✅"*30)
    print("  All tests completed!")
    print("✅"*30)
    print("\nCheck the output above for any errors.")
    print("You can now explore the API at: http://localhost:8000/api/")
    print("Or use the admin panel at: http://localhost:8000/admin/")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
