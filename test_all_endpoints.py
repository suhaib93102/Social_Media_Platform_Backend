"""
Comprehensive test script for all Pinmate API endpoints
Tests: Email/Phone Signup, Email/Phone Login, Guest Login, Get Interests, Setup Profile, Get Feed
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"  # Change to deployed URL when testing production

# Test data
test_email = "testuser@example.com"
test_phone = "9876543210"
test_password = "Test@1234"


def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*60}\n")


def test_signup_email():
    """Test signup with email"""
    print("\n🔵 Testing Email Signup...")
    
    payload = {
        "email_id": test_email,
        "password": test_password,
        "lat": "28.7041",
        "long": "77.1025",
        "interests": ["technology", "music", "travel"]
    }
    
    response = requests.post(f"{BASE_URL}/auth/signup/", json=payload)
    print_response("EMAIL SIGNUP", response)
    
    if response.status_code == 201:
        data = response.json()
        return data['tokens']['access']
    return None


def test_signup_phone():
    """Test signup with phone number"""
    print("\n🔵 Testing Phone Signup...")
    
    payload = {
        "number": test_phone,
        "password": test_password,
        "lat": "12.9716",
        "long": "77.5946",
        "interests": ["sports", "photography", "food"]
    }
    
    response = requests.post(f"{BASE_URL}/auth/signup/", json=payload)
    print_response("PHONE SIGNUP", response)
    
    if response.status_code == 201:
        data = response.json()
        return data['tokens']['access']
    return None


def test_login_email():
    """Test login with email"""
    print("\n🔵 Testing Email Login...")
    
    payload = {
        "email_id": test_email,
        "password": test_password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login/", json=payload)
    print_response("EMAIL LOGIN", response)
    
    if response.status_code == 200:
        data = response.json()
        return data['tokens']['access']
    return None


def test_login_phone():
    """Test login with phone"""
    print("\n🔵 Testing Phone Login...")
    
    payload = {
        "number": test_phone,
        "password": test_password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login/", json=payload)
    print_response("PHONE LOGIN", response)
    
    if response.status_code == 200:
        data = response.json()
        return data['tokens']['access']
    return None


def test_get_interests():
    """Test get interests endpoint"""
    print("\n🔵 Testing Get Interests...")
    
    payload = {
        "lat": "28.7041",
        "long": "77.1025"
    }
    
    response = requests.post(f"{BASE_URL}/get-interests/", json=payload)
    print_response("GET INTERESTS", response)


def test_guest_login():
    """Test guest login"""
    print("\n🔵 Testing Guest Login...")
    
    payload = {
        "interests": ["Art", "Travel", "Food", "Technology"],
        "lat": "28.613939",
        "long": "77.209021"
    }
    
    response = requests.post(f"{BASE_URL}/login/guest/", json=payload)
    print_response("GUEST LOGIN", response)
    
    if response.status_code == 201:
        data = response.json()
        return data['tokens']['access']
    return None


def test_setup_profile(access_token):
    """Test setup profile endpoint"""
    print("\n🔵 Testing Setup Profile...")
    
    payload = {
        "name": "Test User",
        "bio": "Software Developer at Pinmate",
        "gender": "Male",
        "age": 25,
        "image_url": "https://example.com/image.jpg",
        "additional_pincodes": ["560001", "560002", "560003"]
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(f"{BASE_URL}/setup-profile/", json=payload, headers=headers)
    print_response("SETUP PROFILE", response)


def test_get_feed(access_token):
    """Test get feed endpoint"""
    print("\n🔵 Testing Get Feed...")
    
    payload = {
        "lat": "37.7749",
        "long": "-122.4194"
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(f"{BASE_URL}/get-feed/", json=payload, headers=headers)
    print_response("GET FEED", response)


def test_token_refresh(refresh_token):
    """Test token refresh endpoint"""
    print("\n🔵 Testing Token Refresh...")
    
    payload = {
        "refresh": refresh_token
    }
    
    response = requests.post(f"{BASE_URL}/auth/token/refresh/", json=payload)
    print_response("TOKEN REFRESH", response)


def populate_interests():
    """Populate sample interests in database (run in Django shell)"""
    print("\n🔵 Populating sample interests...")
    print("""
    Run this in Django shell (python manage.py shell):
    
    from api.models import Interest
    
    interests_data = [
        {"interest_id": "technology", "name": "Technology", "image": "https://example.com/images/technology.jpg"},
        {"interest_id": "art", "name": "Art", "image": "https://example.com/images/art.jpg"},
        {"interest_id": "travel", "name": "Travel", "image": "https://example.com/images/travel.jpg"},
        {"interest_id": "music", "name": "Music", "image": "https://example.com/images/music.jpg"},
        {"interest_id": "sports", "name": "Sports", "image": "https://example.com/images/sports.jpg"},
        {"interest_id": "food", "name": "Food", "image": "https://example.com/images/food.jpg"},
        {"interest_id": "photography", "name": "Photography", "image": "https://example.com/images/photography.jpg"},
        {"interest_id": "fashion", "name": "Fashion", "image": "https://example.com/images/fashion.jpg"},
        {"interest_id": "fitness", "name": "Fitness", "image": "https://example.com/images/fitness.jpg"},
        {"interest_id": "diy", "name": "DIY", "image": "https://example.com/images/diy.jpg"},
    ]
    
    for item in interests_data:
        Interest.objects.get_or_create(**item)
    
    print("Interests populated!")
    """)


def run_all_tests():
    """Run all test cases"""
    print("\n" + "="*60)
    print("🚀 PINMATE API ENDPOINT TESTS")
    print("="*60)
    
    # Populate interests instruction
    populate_interests()
    
    # Test signup
    email_token = test_signup_email()
    
    # Test login (if signup failed, try login with existing user)
    if not email_token:
        email_token = test_login_email()
    
    # Test phone signup
    phone_token = test_signup_phone()
    
    # Test phone login (if signup failed)
    if not phone_token:
        phone_token = test_login_phone()
    
    # Test get interests
    test_get_interests()
    
    # Test guest login
    guest_token = test_guest_login()
    
    # Test setup profile (using email token if available)
    if email_token:
        test_setup_profile(email_token)
    elif phone_token:
        test_setup_profile(phone_token)
    elif guest_token:
        test_setup_profile(guest_token)
    
    # Test get feed
    if email_token:
        test_get_feed(email_token)
    elif phone_token:
        test_get_feed(phone_token)
    elif guest_token:
        test_get_feed(guest_token)
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
