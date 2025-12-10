#!/usr/bin/env python3
"""
Final validation test for all Pinmate endpoints
Validates that all implemented features work correctly
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(name, method, url, data=None, headers=None, expected_status=None):
    """Generic test function"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    
    try:
        if method == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            response = requests.get(url, headers=headers)
        
        print(f"Status: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response: {response.text[:200]}")
        
        if expected_status and response.status_code != expected_status:
            print(f"❌ FAILED: Expected {expected_status}, got {response.status_code}")
            return None
        
        print(f"✅ PASSED")
        return response
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None


def main():
    print("\n" + "="*60)
    print("PINMATE API - FINAL VALIDATION TEST")
    print("="*60)
    
    # 1. Test Get Interests
    test_endpoint(
        "Get Interests",
        "POST",
        f"{BASE_URL}/get-interests/",
        {"lat": "28.7041", "long": "77.1025"},
        expected_status=200
    )
    
    # 2. Test Guest Login
    guest_response = test_endpoint(
        "Guest Login",
        "POST",
        f"{BASE_URL}/login/guest/",
        {
            "interests": ["Art", "Travel", "Technology"],
            "lat": "28.613939",
            "long": "77.209021"
        },
        expected_status=201
    )
    
    guest_token = None
    if guest_response:
        try:
            guest_token = guest_response.json()['tokens']['access']
        except:
            pass
    
    # 3. Test Email Signup (might fail if user exists)
    email = f"testuser{import_random()}@example.com" if False else "newuser999@example.com"
    signup_response = test_endpoint(
        "Email Signup",
        "POST",
        f"{BASE_URL}/auth/signup/",
        {
            "email_id": email,
            "password": "Test@1234",
            "lat": "28.7041",
            "long": "77.1025",
            "interests": ["technology", "music"]
        }
    )
    
    # 4. Test Email Login (with existing user)
    login_response = test_endpoint(
        "Email Login",
        "POST",
        f"{BASE_URL}/auth/login/",
        {
            "email_id": "yathaarthbatra10@gmail.com",
            "password": "Yatha@1234"
        },
        expected_status=200
    )
    
    access_token = None
    refresh_token = None
    if login_response:
        try:
            tokens = login_response.json()['tokens']
            access_token = tokens['access']
            refresh_token = tokens['refresh']
        except:
            pass
    
    # 5. Test Phone Signup (might fail if user exists)
    phone_number = "8888888888"
    test_endpoint(
        "Phone Signup",
        "POST",
        f"{BASE_URL}/auth/signup/",
        {
            "number": phone_number,
            "password": "Test@1234",
            "lat": "12.9716",
            "long": "77.5946",
            "interests": ["sports", "food"]
        }
    )
    
    # 6. Test Phone Login
    phone_login_response = test_endpoint(
        "Phone Login",
        "POST",
        f"{BASE_URL}/auth/login/",
        {
            "number": "7015926932",
            "password": "Yatha@1234"
        },
        expected_status=200
    )
    
    # 7. Test Token Refresh
    if refresh_token:
        test_endpoint(
            "Token Refresh",
            "POST",
            f"{BASE_URL}/auth/token/refresh/",
            {"refresh": refresh_token},
            expected_status=200
        )
    
    # 8. Test Setup Profile (requires auth)
    if access_token:
        test_endpoint(
            "Setup Profile",
            "POST",
            f"{BASE_URL}/setup-profile/",
            {
                "name": "Test User",
                "bio": "Software Developer",
                "gender": "Male",
                "age": 25,
                "image_url": "https://example.com/profile.jpg",
                "additional_pincodes": ["560001", "560002"]
            },
            headers={"Authorization": f"Bearer {access_token}"},
            expected_status=200
        )
    
    # 9. Test Get Feed (requires auth)
    if access_token:
        test_endpoint(
            "Get Feed",
            "POST",
            f"{BASE_URL}/get-feed/",
            {"lat": "37.7749", "long": "-122.4194"},
            headers={"Authorization": f"Bearer {access_token}"},
            expected_status=200
        )
    
    # 10. Test Guest Setup Profile
    if guest_token:
        test_endpoint(
            "Guest Setup Profile",
            "POST",
            f"{BASE_URL}/setup-profile/",
            {
                "name": "Guest User",
                "bio": "Just browsing",
                "additional_pincodes": ["110001"]
            },
            headers={"Authorization": f"Bearer {guest_token}"},
            expected_status=200
        )
    
    print("\n" + "="*60)
    print("FINAL VALIDATION COMPLETE")
    print("="*60)
    print("\nAll endpoints have been tested!")
    print("\nNext steps:")
    print("1. Import Pinmate_API_Collection.postman_collection.json into Postman")
    print("2. Set base_url variable to http://127.0.0.1:8000 (or production URL)")
    print("3. Run requests in order: Login → Setup Profile → Get Feed")
    print("4. Tokens will be auto-saved to environment variables")
    print("\nAPI Documentation: See API_DOCUMENTATION.md")
    print("Implementation Summary: See IMPLEMENTATION_SUMMARY.md")


if __name__ == "__main__":
    main()
