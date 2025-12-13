#!/bin/bash

# Pinmate API Onboarding - Comprehensive Test Script
# This script tests all onboarding endpoints

BASE_URL="http://localhost:8000"
TIMESTAMP=$(date +%s)
TEST_EMAIL="testuser${TIMESTAMP}@example.com"
TEST_PHONE="98765$(echo $TIMESTAMP | tail -c 6)"

echo "========================================="
echo "Pinmate API Onboarding - Test Suite"
echo "========================================="
echo "Timestamp: $TIMESTAMP"
echo "Test Email: $TEST_EMAIL"
echo "Test Phone: $TEST_PHONE"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test 1: Get Interests
echo -e "${BLUE}Test 1: GET Interests${NC}"
curl -X POST $BASE_URL/get-interests/ \
  -H "Content-Type: application/json" \
  -d '{"lat": "28.6139", "long": "77.2090"}' \
  -w "\nStatus: %{http_code}\n\n"

# Test 2: Signup with Email (Debug Mode)
echo -e "${BLUE}Test 2: Signup with Email (Debug Mode)${NC}"
SIGNUP_RESPONSE=$(curl -s -X POST $BASE_URL/auth/signup/ \
  -H "Content-Type: application/json" \
  -H "Is-Debug: true" \
  -d "{
    \"email_id\": \"$TEST_EMAIL\",
    \"password\": \"Test@1234\",
    \"lat\": \"28.6139\",
    \"long\": \"77.2090\",
    \"interests\": [\"technology\", \"music\", \"travel\"]
  }")

echo "$SIGNUP_RESPONSE" | python3 -m json.tool
ACCESS_TOKEN=$(echo "$SIGNUP_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['tokens']['access'])" 2>/dev/null)
echo -e "\nAccess Token: $ACCESS_TOKEN\n"

# Test 3: Save Interests
echo -e "${BLUE}Test 3: Save Interests${NC}"
curl -X POST $BASE_URL/save-interests/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"interests": ["tech", "sports", "entertainment"]}' \
  -w "\nStatus: %{http_code}\n\n"

# Test 4: Setup Profile
echo -e "${BLUE}Test 4: Setup Profile with Address${NC}"
curl -X POST $BASE_URL/setup-profile/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "name": "Yathaarth Batra",
    "bio": "Software Developer at Pinmate",
    "gender": "Male",
    "age": 25,
    "image_url": "https://example.com/profile.jpg",
    "additional_pincodes": ["560002", "560003", "560004"],
    "address_details": "123 Main Street, Apartment 4B, Near City Center"
  }' \
  -w "\nStatus: %{http_code}\n\n"

# Test 5: Signup with Phone (Production Mode - OTP Required)
echo -e "${BLUE}Test 5: Signup with Phone (Production Mode)${NC}"
OTP_RESPONSE=$(curl -s -X POST $BASE_URL/auth/signup/ \
  -H "Content-Type: application/json" \
  -H "Is-Debug: false" \
  -d "{
    \"number\": \"$TEST_PHONE\",
    \"password\": \"Test@1234\",
    \"lat\": \"28.6139\",
    \"long\": \"77.2090\",
    \"interests\": [\"technology\", \"music\"]
  }")

echo "$OTP_RESPONSE" | python3 -m json.tool
echo -e "\n${RED}Note: OTP is printed in server console. Check terminal running Django server.${NC}\n"

# Test 6: Guest Login
echo -e "${BLUE}Test 6: Guest Login${NC}"
GUEST_RESPONSE=$(curl -s -X POST $BASE_URL/login/guest/ \
  -H "Content-Type: application/json" \
  -H "Is-Debug: true" \
  -d '{
    "interests": ["Art", "Travel", "Food", "Technology"],
    "lat": "28.6139",
    "long": "77.2090"
  }')

echo "$GUEST_RESPONSE" | python3 -m json.tool
GUEST_TOKEN=$(echo "$GUEST_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['tokens']['access'])" 2>/dev/null)
echo -e "\nGuest Access Token: $GUEST_TOKEN\n"

# Test 7: Get Feed (with authentication)
echo -e "${BLUE}Test 7: Get Feed${NC}"
curl -X POST $BASE_URL/get-feed/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"lat": "37.7749", "long": "-122.4194"}' \
  -w "\nStatus: %{http_code}\n\n"

# Test 8: Login with Email
echo -e "${BLUE}Test 8: Login with Email${NC}"
curl -X POST $BASE_URL/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{
    \"email_id\": \"$TEST_EMAIL\",
    \"password\": \"Test@1234\"
  }" \
  -w "\nStatus: %{http_code}\n\n"

# Test 9: Validation - Invalid Phone
echo -e "${BLUE}Test 9: Validation - Invalid Phone Number${NC}"
curl -X POST $BASE_URL/auth/signup/ \
  -H "Content-Type: application/json" \
  -H "Is-Debug: true" \
  -d '{
    "number": "123",
    "password": "Test@1234",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": ["technology"]
  }' \
  -w "\nStatus: %{http_code}\n\n"

# Test 10: Validation - Invalid Coordinates
echo -e "${BLUE}Test 10: Validation - Invalid Coordinates${NC}"
curl -X POST $BASE_URL/get-interests/ \
  -H "Content-Type: application/json" \
  -d '{"lat": "91.5", "long": "200.5"}' \
  -w "\nStatus: %{http_code}\n\n"

echo -e "${GREEN}========================================="
echo "Test Suite Completed"
echo "=========================================${NC}"
