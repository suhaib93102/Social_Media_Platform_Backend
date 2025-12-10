import requests
import json


# DEPLOYED BACKEND URL
BASE_URL = "https://social-media-platform-backend-4oz4.onrender.com"
# BASE_URL = "http://127.0.0.1:8000"


# -------------------------------
#  SIGNUP TEST
# -------------------------------
def test_signup():
    url = f"{BASE_URL}/auth/signup/"
    payload = {
        "userId": "authuser001",
        "name": "Test User",
        "email": "authuser001@example.com",
        "password": "SecurePassword123!"
    }

    print("\n🔹 Testing SIGNUP...")
    response = requests.post(url, json=payload)

    print("Status Code:", response.status_code)
    try:
        print("Response:", response.json())
    except:
        print("Raw Response:", response.text)

    return response


# -------------------------------
#  LOGIN TEST
# -------------------------------
def test_login():
    url = f"{BASE_URL}/auth/login/"
    payload = {
        "userId": "authuser001",
        "password": "SecurePassword123!"
    }

    print("\n🔹 Testing LOGIN...")
    response = requests.post(url, json=payload)

    print("Status Code:", response.status_code)
    try:
        print("Response:", response.json())
    except:
        print("Raw Response:", response.text)

    return response



if __name__ == "__main__":
    print("\n==============================")
    print("   SIMPLE AUTH TEST SCRIPT")
    print("==============================")

    # Test Signup
    test_signup()

    # Test Login
    test_login()
