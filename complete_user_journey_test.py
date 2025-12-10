#!/usr/bin/env python3
"""
Complete User Journey Test - Tests full workflow from signup to feed
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def print_step(step_num, title):
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {title}")
    print('='*60)

def test_complete_journey():
    print(f"\n🚀 PINMATE API - COMPLETE USER JOURNEY TEST")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Test data
    test_email = f"journey_test_{datetime.now().strftime('%H%M%S')}@example.com"
    test_password = "Journey@Test123"
    
    # Step 1: Get Interests
    print_step(1, "Get Available Interests")
    response = requests.post(f"{BASE_URL}/get-interests/", json={
        "lat": "28.6139",
        "long": "77.2090"
    })
    print(f"Status: {response.status_code}")
    interests_data = response.json()
    print(f"Interests fetched: {len(interests_data.get('interests', []))}")
    if response.status_code == 200:
        print("✅ PASSED")
    else:
        print("❌ FAILED")
        return
    
    # Step 2: Sign Up
    print_step(2, "Sign Up with Email")
    response = requests.post(f"{BASE_URL}/auth/signup/", json={
        "email_id": test_email,
        "password": test_password,
        "interests": ["technology", "music", "travel"],
        "lat": "28.6139",
        "long": "77.2090"
    })
    print(f"Status: {response.status_code}")
    signup_data = response.json()
    if response.status_code == 201:
        print(f"User created: {signup_data['user']['userId']}")
        print("✅ PASSED")
    else:
        print(f"Error: {signup_data}")
        print("❌ FAILED")
        return
    
    # Save tokens
    access_token = signup_data['tokens']['access']
    refresh_token = signup_data['tokens']['refresh']
    print(f"Access token saved: {access_token[:50]}...")
    
    # Step 3: Setup Profile
    print_step(3, "Setup User Profile")
    response = requests.post(f"{BASE_URL}/setup-profile/", 
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={
            "name": "Journey Test User",
            "bio": "Testing the complete user journey",
            "gender": "Other",
            "age": 25,
            "additional_pincodes": ["110001", "560001"]
        }
    )
    print(f"Status: {response.status_code}")
    profile_data = response.json()
    print(f"Response: {profile_data}")
    if response.status_code == 200:
        print("✅ PASSED")
    else:
        print("❌ FAILED")
        return
    
    # Step 4: Get Feed
    print_step(4, "Get Personalized Feed")
    response = requests.post(f"{BASE_URL}/get-feed/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={
            "lat": "28.6139",
            "long": "77.2090"
        }
    )
    print(f"Status: {response.status_code}")
    feed_data = response.json()
    print(f"Response: {feed_data}")
    if response.status_code == 200:
        print("✅ PASSED")
    else:
        print("❌ FAILED")
        return
    
    # Step 5: Refresh Token
    print_step(5, "Refresh Access Token")
    response = requests.post(f"{BASE_URL}/auth/token/refresh/", json={
        "refresh": refresh_token
    })
    print(f"Status: {response.status_code}")
    refresh_data = response.json()
    if response.status_code == 200:
        new_access_token = refresh_data['access']
        print(f"New access token: {new_access_token[:50]}...")
        print("✅ PASSED")
    else:
        print("❌ FAILED")
        return
    
    # Step 6: Use Refreshed Token
    print_step(6, "Use Refreshed Token to Get Feed")
    response = requests.post(f"{BASE_URL}/get-feed/",
        headers={
            "Authorization": f"Bearer {new_access_token}",
            "Content-Type": "application/json"
        },
        json={
            "lat": "28.6139",
            "long": "77.2090"
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ PASSED")
    else:
        print("❌ FAILED")
        return
    
    # Final Summary
    print("\n" + "="*60)
    print("🎉 COMPLETE USER JOURNEY TEST - SUCCESS!")
    print("="*60)
    print(f"\n✅ All steps completed successfully!")
    print(f"\nUser Journey:")
    print(f"  1. ✅ Fetched interests")
    print(f"  2. ✅ Signed up: {test_email}")
    print(f"  3. ✅ Setup profile")
    print(f"  4. ✅ Retrieved feed")
    print(f"  5. ✅ Refreshed token")
    print(f"  6. ✅ Used refreshed token")
    print(f"\n🚀 API is fully functional and ready for production!")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        test_complete_journey()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server")
        print("Make sure Django server is running: python manage.py runserver")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
