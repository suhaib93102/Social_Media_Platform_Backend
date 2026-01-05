#!/bin/bash

# Test script for the API endpoints
BASE_URL="http://127.0.0.1:8000/api"

echo "🧪 Testing API Endpoints"
echo "========================"

# Test 0: Create Test User (Debug Mode)
echo ""
echo "0. Creating test user (debug mode):"
TEST_EMAIL="testuser$(date +%s)@example.com"
echo "curl -X POST \"$BASE_URL/auth/signup/\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"x-device-id: test-device-$(date +%s)\" \\"
echo "  -H \"app-mode: debug\" \\"
echo "  -H \"x-debug: true\" \\"
echo "  -d '{\"email_id\": \"$TEST_EMAIL\", \"password\": \"password123\", \"lat\": \"28.6139\", \"long\": \"77.2090\", \"interests\": [\"technology\", \"sports\"]}' | jq '.tokens.access'"
DEVICE_ID="test-device-$(date +%s)"
ACCESS_TOKEN=$(curl -X POST "$BASE_URL/auth/signup/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: $DEVICE_ID" \
  -H "app-mode: debug" \
  -H "x-debug: true" \
  -d "{\"email_id\": \"$TEST_EMAIL\", \"password\": \"password123\", \"lat\": \"28.6139\", \"long\": \"77.2090\", \"interests\": [\"technology\", \"sports\"]}" 2>/dev/null | jq -r '.tokens.access')

if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Failed to create test user"
    echo "💡 Trying to login with existing user..."
    ACCESS_TOKEN=$(curl -X POST "$BASE_URL/auth/login/" \
      -H "Content-Type: application/json" \
      -d "{\"email_id\": \"$TEST_EMAIL\", \"password\": \"password123\"}" 2>/dev/null | jq -r '.tokens.access')
fi

if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Cannot get access token - skipping authenticated tests"
    AUTH_READY=false
else
    echo "✅ Got access token: ${ACCESS_TOKEN:0:50}..."
    AUTH_READY=true
fi

# Test 1: Create Post Screen (GET /create-post/)
echo ""
echo "1. Testing /create-post/ endpoint (GET):"
echo "curl -X GET \"$BASE_URL/create-post/\" | jq '.results[0].type'"
curl -X GET "$BASE_URL/create-post/" 2>/dev/null | jq '.results[0].type' || echo "❌ Failed to test create-post endpoint"

# Test 2: Home Feed (POST /home-feed/)
echo ""
echo "2. Testing /home-feed/ endpoint (POST):"
echo "curl -X POST \"$BASE_URL/home-feed/\" \\
  -H \"Content-Type: application/json\" \\
  -d '{\"page_id\": 0, \"limit\": 10}' | jq '.results[0].type'"
curl -X POST "$BASE_URL/home-feed/" \
  -H "Content-Type: application/json" \
  -d '{"page_id": 0, "limit": 10}' 2>/dev/null | jq '.results[0].type' || echo "❌ Failed to test home-feed endpoint"

# Test 3: Login to get authentication token (only if needed)
if [ "$AUTH_READY" = false ]; then
    echo ""
    echo "3. Testing /auth/login/ endpoint (POST) - Getting auth token:"
    echo "curl -X POST \"$BASE_URL/auth/login/\" \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -d '{\"email_id\": \"$TEST_EMAIL\", \"password\": \"password123\"}' | jq '.tokens.access'"
    ACCESS_TOKEN=$(curl -X POST "$BASE_URL/auth/login/" \
      -H "Content-Type: application/json" \
      -d "{\"email_id\": \"$TEST_EMAIL\", \"password\": \"password123\"}" 2>/dev/null | jq -r '.tokens.access')

    if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
        echo "❌ Login failed - cannot test save-post endpoint"
        echo "💡 Note: You may need to create a test user first or use valid credentials"
        AUTH_READY=false
    else
        echo "✅ Got access token: ${ACCESS_TOKEN:0:50}..."
        AUTH_READY=true
    fi
fi

# Test 4: Save Post (POST /save-post/) with authentication
if [ "$AUTH_READY" = true ]; then
    echo ""
    echo "4. Testing /save-post/ endpoint (POST) with authentication:"
    echo "curl -X POST \"$BASE_URL/save-post/\" \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -H \"Authorization: Bearer $ACCESS_TOKEN\" \\"
    echo "  -d '{
    \"post_type\": \"post\",
    \"content\": \"This is a test post from curl!\",
    \"pincode_id\": \"pincode_home_201301\"
  }' | jq '.message'"
    curl -X POST "$BASE_URL/save-post/" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -d '{
        "post_type": "post",
        "content": "This is a test post from curl!",
        "pincode_id": "pincode_home_201301"
      }' 2>/dev/null | jq '.message' || echo "❌ Failed to test save-post endpoint"
fi

echo ""
echo "🎉 Testing complete!"
echo ""
echo "📝 Notes:"
echo "- Make sure Django server is running on port 8000"
echo "- Test user created: testuser@example.com / password123"
echo "- You can modify the test data as needed"