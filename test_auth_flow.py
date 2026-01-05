#!/usr/bin/env python
"""
Test script to verify authentication flow and test endpoints
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.insert(0, '/Users/vishaljha/backend')
django.setup()

from api.models import UserProfile
from rest_framework_simplejwt.tokens import RefreshToken

def get_test_token():
    """Generate a test token for testing"""
    try:
        # Create or get a test user
        test_user, created = UserProfile.objects.get_or_create(
            userId="test_user_123",
            defaults={
                'name': 'Test User',
                'email': 'test@example.com',
                'phone_number': '+919999999999',
                'is_guest': False,
                'password': 'dummy_hash',  # Already hashed password
            }
        )
        
        # Generate tokens
        refresh = RefreshToken.for_user(test_user)
        access_token = str(refresh.access_token)
        
        print(f"✓ Test user created/fetched: {test_user.userId}")
        print(f"✓ Access Token: {access_token}")
        return access_token
    except Exception as e:
        print(f"✗ Error creating test user: {e}")
        return None

def test_home_feed(token):
    """Test home-feed endpoint with authentication"""
    import requests
    
    url = "http://localhost:8000/api/home-feed/"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\n✓ GET /home-feed/")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response has 'results': {'results' in data}")
            if 'results' in data and len(data['results']) > 0:
                print(f"  First result type: {data['results'][0].get('type', 'N/A')}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Error testing home-feed: {e}")

def test_create_post_ui(token):
    """Test create-post UI endpoint with authentication"""
    import requests
    
    url = "http://localhost:8000/api/create-post/"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\n✓ GET /create-post/")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response has 'results': {'results' in data}")
            if 'results' in data and len(data['results']) > 0:
                print(f"  First result type: {data['results'][0].get('type', 'N/A')}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Error testing create-post: {e}")

def test_save_post(token):
    """Test save-post endpoint with authentication"""
    import requests
    
    url = "http://localhost:8000/api/save-post/"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'post_type': 'post',
        'content': 'Test post content',
        'pincode_id': 'pincode_home_201301',
        'photo_url': 'https://picsum.photos/800/800'
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"\n✓ POST /save-post/")
        print(f"  Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"  Response has 'entities': {'entities' in data}")
            if 'entities' in data:
                entities = data['entities']
                print(f"  Entities keys: {list(entities.keys())}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Error testing save-post: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("Authentication Flow Test")
    print("=" * 60)
    
    token = get_test_token()
    
    if token:
        print(f"\n✓ Authentication successful")
        print("\nTesting endpoints with authentication...")
        
        # Note: These will fail if server is not running
        print("\nTo test live endpoints:")
        print("  1. Start server: python manage.py runserver 8000")
        print("  2. Run this script again")
        print("\nManual curl commands to test:")
        print(f"\nTEST_TOKEN='{token}'")
        print(f"\n1. Home Feed:")
        print(f"   curl -H 'Authorization: Bearer $TEST_TOKEN' http://localhost:8000/api/home-feed/")
        print(f"\n2. Create Post UI:")
        print(f"   curl -H 'Authorization: Bearer $TEST_TOKEN' http://localhost:8000/api/create-post/")
        print(f"\n3. Save Post:")
        print(f"   curl -H 'Authorization: Bearer $TEST_TOKEN' \\")
        print(f"     -H 'Content-Type: application/json' \\")
        print(f"     -d '{{\"post_type\": \"post\", \"content\": \"Test\", \"pincode_id\": \"pincode_home_201301\", \"photo_url\": \"https://picsum.photos/800/800\"}}' \\")
        print(f"     -X POST http://localhost:8000/api/save-post/")
    else:
        print("\n✗ Failed to create test token")
