import requests
import json
import sys

BASE_URL = "http://localhost:8000"
USERNAME = "udaya1"
PASSWORD = "123"

def login():
    # Try creating a fresh user to guarantee access
    import time
    email = f"dash_test_{int(time.time())}@test.com"
    password = "password123"
    
    print(f"👤 Registering temp user: {email}")
    try:
        reg_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email, 
            "password": password, 
            "full_name": "Dashboard Tester", 
            "role": "dispatcher", 
            "hospital_id": "none"
        })
        
        # If registration fails (e.g. exists), just try login
        if reg_res.status_code not in [200, 400]:
             print(f"⚠️ Registration warning: {reg_res.status_code}")
             
        print("🔑 Logging in...")
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Login Successful")
            return response.json()["access_token"]
        else:
            print(f"❌ Login Failed: {response.status_code} - {response.text}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        sys.exit(1)

def check_dashboard(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔍 Checking Dashboard Stats (/api/dashboard/stats)...")
    try:
        resp = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            print("✅ Stats Response:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Stats Failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Stats Request Error: {e}")

    print("\n🔍 Checking Recent Bookings (/api/dashboard/recent-bookings)...")
    try:
        resp = requests.get(f"{BASE_URL}/api/dashboard/recent-bookings", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Recent Bookings Found: {len(data)}")
            if len(data) > 0:
                print("Sample Booking:")
                print(json.dumps(data[0], indent=2))
        else:
            print(f"❌ Recent Bookings Failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Recent Bookings Request Error: {e}")

    print("\n🔍 Checking Activity Transfers (/api/dashboard/activity-transfers)...")
    try:
        resp = requests.get(f"{BASE_URL}/api/dashboard/activity-transfers", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            print("✅ Activity Transfers Response:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Activity Transfers Failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Activity Transfers Request Error: {e}")

if __name__ == "__main__":
    token = login()
    check_dashboard(token)
