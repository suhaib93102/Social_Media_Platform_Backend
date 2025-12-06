#!/usr/bin/env python3
"""
Comprehensive API Endpoint Testing Script
Tests all endpoints for the Social App API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_endpoint(method, url, data=None, description=""):
    """Test a single endpoint"""
    print(f"\n🧪 Testing: {description}")
    print(f"   {method} {url}")

    try:
        if method.upper() == 'GET':
            response = requests.get(url, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, timeout=10)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, json=data, timeout=10)
        else:
            print(f"   ❌ Unsupported method: {method}")
            return False

        print(f"   Status: {response.status_code}")

        if response.status_code in [200, 201]:
            print("   ✅ SUCCESS")
            try:
                result = response.json()
                if isinstance(result, list):
                    print(f"   📊 Returned {len(result)} items")
                elif isinstance(result, dict):
                    print(f"   📋 Response keys: {list(result.keys())}")
                else:
                    print(f"   📝 Response: {str(result)[:100]}...")
            except:
                print(f"   📄 Response: {response.text[:100]}...")
            return True
        else:
            print(f"   ❌ FAILED: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

def main():
    print("🚀 Starting Social App API Endpoint Tests")
    print("=" * 50)

    # Test data
    test_user_data = {
        "userId": "test_user_123",
        "name": "Test User",
        "email": "test@example.com",
        "gender": "male",
        "age": 25,
        "bio": "Test bio",
        "profilePhoto": "https://example.com/photo.jpg",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "activePincodes": ["110001", "110002"],
        "followers": [],
        "following": [],
        "idCardUrl": "https://example.com/id.jpg"
    }

    test_post_data = {
        "description": "Test post",
        "mediaType": "image",
        "mediaURL": "https://example.com/image.jpg",
        "pincode": "110001",
        "userId": "test_user_123",
        "location": {
            "accuracy": 10.5,
            "altitude": 100.0,
            "altitudeAccuracy": 5.0,
            "heading": 90.0,
            "latitude": 28.6139,
            "longitude": 77.2090,
            "speed": 0.0
        }
    }

    test_follow_request_data = {
        "fromUserId": "test_user_123",
        "toUserId": "test_user_456"
    }

    test_story_data = {
        "description": "Test story",
        "mediaType": "image",
        "mediaURL": "https://example.com/story.jpg",
        "userId": "test_user_123",
        "expireAt": "2025-12-31T23:59:59Z"
    }

    test_chat_data = {
        "users": ["test_user_123", "test_user_456"]
    }

    # Track created IDs for dependent tests
    created_user_id = None
    created_post_id = None
    created_follow_request_id = None
    created_story_id = None
    created_chat_id = None

    results = []

    # 1. Test User Endpoints
    print("\n👤 USER ENDPOINTS")
    print("-" * 30)

    # Create user
    success = test_endpoint(
        'POST', f"{BASE_URL}/users/",
        test_user_data,
        "Create User Profile"
    )
    results.append(("Create User", success))
    if success:
        created_user_id = test_user_data['userId']

    # Get user profile
    if created_user_id:
        success = test_endpoint(
            'GET', f"{BASE_URL}/users/{created_user_id}/",
            description="Get User Profile"
        )
        results.append(("Get User Profile", success))

        # Get user following
        success = test_endpoint(
            'GET', f"{BASE_URL}/users/{created_user_id}/following/",
            description="Get User Following"
        )
        results.append(("Get User Following", success))

        # Get user followers
        success = test_endpoint(
            'GET', f"{BASE_URL}/users/{created_user_id}/followers/",
            description="Get User Followers"
        )
        results.append(("Get User Followers", success))

    # 2. Test Follow Request Endpoints
    print("\n🤝 FOLLOW REQUEST ENDPOINTS")
    print("-" * 30)

    # Create follow request
    success = test_endpoint(
        'POST', f"{BASE_URL}/followRequests/",
        test_follow_request_data,
        "Create Follow Request"
    )
    results.append(("Create Follow Request", success))

    # Get follow requests (assuming we can get the first one)
    success = test_endpoint(
        'GET', f"{BASE_URL}/followRequests/1/",
        description="Get Follow Request"
    )
    results.append(("Get Follow Request", success))

    # Update follow request status
    success = test_endpoint(
        'PATCH', f"{BASE_URL}/followRequests/1/",
        {"status": "accepted"},
        "Update Follow Request Status"
    )
    results.append(("Update Follow Request", success))

    # 3. Test Post Endpoints
    print("\n📸 POST ENDPOINTS")
    print("-" * 30)

    # Create post
    success = test_endpoint(
        'POST', f"{BASE_URL}/posts/",
        test_post_data,
        "Create Post"
    )
    results.append(("Create Post", success))

    # Get posts (assuming we can get the first one)
    success = test_endpoint(
        'GET', f"{BASE_URL}/posts/1/",
        description="Get Post"
    )
    results.append(("Get Post", success))

    # Get user posts
    if created_user_id:
        success = test_endpoint(
            'GET', f"{BASE_URL}/users/{created_user_id}/posts/",
            description="Get User Posts"
        )
        results.append(("Get User Posts", success))

    # 4. Test Story Endpoints
    print("\n📖 STORY ENDPOINTS")
    print("-" * 30)

    # Create story
    success = test_endpoint(
        'POST', f"{BASE_URL}/stories/",
        test_story_data,
        "Create Story"
    )
    results.append(("Create Story", success))

    # Get story
    success = test_endpoint(
        'GET', f"{BASE_URL}/stories/1/",
        description="Get Story"
    )
    results.append(("Get Story", success))

    # Get user stories
    if created_user_id:
        success = test_endpoint(
            'GET', f"{BASE_URL}/users/{created_user_id}/stories/",
            description="Get User Stories"
        )
        results.append(("Get User Stories", success))

    # 5. Test Chat Endpoints
    print("\n💬 CHAT ENDPOINTS")
    print("-" * 30)

    # Create chat
    success = test_endpoint(
        'POST', f"{BASE_URL}/chats/",
        test_chat_data,
        "Create Chat"
    )
    results.append(("Create Chat", success))

    # Get chat
    success = test_endpoint(
        'GET', f"{BASE_URL}/chats/1/",
        description="Get Chat"
    )
    results.append(("Get Chat", success))

    # Get chat messages
    success = test_endpoint(
        'GET', f"{BASE_URL}/chats/1/messages/",
        description="Get Chat Messages"
    )
    results.append(("Get Chat Messages", success))

    # Send message
    success = test_endpoint(
        'POST', f"{BASE_URL}/chats/1/messages/",
        {
            "senderId": "test_user_123",
            "content": "Hello, this is a test message!"
        },
        "Send Message"
    )
    results.append(("Send Message", success))

    # 6. Test Follower Endpoints
    print("\n👥 FOLLOWER ENDPOINTS")
    print("-" * 30)

    # Get followers
    success = test_endpoint(
        'GET', f"{BASE_URL}/followers/1/",
        description="Get Follower Relationship"
    )
    results.append(("Get Follower", success))

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("🎉 All API endpoints are working correctly!")
    else:
        print("⚠️  Some endpoints need attention.")

    print("\n🔧 NEXT STEPS:")
    print("1. Fix any failing endpoints above")
    print("2. Switch from SQLite to Supabase PostgreSQL:")
    print("   - Update .env with correct SUPABASE_DB_PASSWORD")
    print("   - Check Supabase dashboard for connection details")
    print("   - Remove IP restrictions if any")
    print("   - Run: python manage.py migrate")

if __name__ == "__main__":
    main()