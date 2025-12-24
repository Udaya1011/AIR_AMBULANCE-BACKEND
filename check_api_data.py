import requests
import json

BASE_URL = "http://localhost:8000"
LOGIN_EMAIL = "testuser_1734892708@example.com" # Use the user created by previous script if possible, or register new
PASSWORD = "password123"

def check_data():
    print("🔍 Checking API Data...")
    
    # 1. Login to get token
    try:
        # Try to login with a known test user, or create one if this fails
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@airswift.com", "password": "demo"})
        
        if login_res.status_code != 200:
             # Fallback to the one created in reproduction script if admin doesn't exist (e.g. udaya1 db)
             # Actually, best to just register a temp checker
             email = f"checker_{int(str(id(object)))}@test.com"
             requests.post(f"{BASE_URL}/api/auth/register", json={
                 "email": email, "password": "password", "full_name": "Checker", "role": "hospital_staff", "hospital_id": "none"
             })
             login_res = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "password"})

        if login_res.status_code != 200:
            print(f"❌ Login Failed: {login_res.text}")
            return

        token = login_res.json()["access_token"]
        print("✅ Login Successful")

        # 2. Get Patients
        headers = {"Authorization": f"Bearer {token}"}
        list_res = requests.get(f"{BASE_URL}/api/patients", headers=headers)
        
        if list_res.status_code == 200:
            patients = list_res.json()
            print(f"✅ Found {len(patients)} patients.")
            if len(patients) > 0:
                print("First patient sample:")
                print(json.dumps(patients[0], indent=2))
        else:
             print(f"❌ List Failed: {list_res.status_code} {list_res.text}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_data()
