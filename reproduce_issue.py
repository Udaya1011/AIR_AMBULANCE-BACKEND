import requests
import time

BASE_URL = "http://localhost:8000"
TEST_EMAIL = f"testuser_{int(time.time())}@example.com"
TEST_PASSWORD = "password123"

def test_flow():
    print(f"🚀 Starting Test Flow with email: {TEST_EMAIL}")

    # 1. Register
    print("\n1. Testing Registration...")
    reg_payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": "Test User",
        "role": "hospital_staff",
        "hospital_id": "none"
    }
    try:
        res = requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload)
        if res.status_code == 200:
            print("✅ Registration Successful")
        else:
            print(f"❌ Registration Failed: {res.status_code} {res.text}")
            return
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    # 2. Login
    print("\n2. Testing Login...")
    login_payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    token = None
    try:
        res = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
        if res.status_code == 200:
            data = res.json()
            token = data.get("access_token")
            print("✅ Login Successful. Token received.")
        else:
            print(f"❌ Login Failed: {res.status_code} {res.text}")
            return
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    # 3. Create Patient
    print("\n3. Testing Create Patient...")
    patient_payload = {
        "full_name": "Test Patient API",
        "date_of_birth": "1990-01-01",
        "gender": "male",
        "weight_kg": 75.0,
        "diagnosis": "API Test Diagnosis",
        "acuity_level": "stable",
        "blood_group": "O+",
        "allergies": [],
        "current_vitals": {},
        "special_equipment_needed": [],
        "insurance_details": {"provider": "A", "policy_number": "1"},
        "next_of_kin": {"name": "B", "relationship": "C", "phone": "1"}
    }
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        res = requests.post(f"{BASE_URL}/api/patients", json=patient_payload, headers=headers)
        if res.status_code == 200:
            print("✅ Patient Creation Successful")
            print(f"   Patient ID: {res.json().get('id')}")
        else:
            print(f"❌ Patient Creation Failed: {res.status_code} {res.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_flow()
