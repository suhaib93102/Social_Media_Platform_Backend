#!/bin/bash

echo "🔍 DEBUGGING PRODUCTION API ISSUES"
echo "======================================================================"
echo ""

BASE="https://social-media-platform-backend-4oz4.onrender.com"
TS=$(date +%s)

# Issue 1: App Init - Check if it's POST or GET
echo "1️⃣  Testing App Init - GET vs POST"
echo "----------------------------------------------------------------------"
echo "GET Request:"
curl -s -X GET "$BASE/app-init/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: debug-test-$TS" \
  -H "x-app-mode: prod" | jq . || echo "$?"

echo ""
echo "POST Request:"
curl -s -X POST "$BASE/app-init/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: debug-test-$TS" \
  -H "x-app-mode: prod" | jq . || echo "$?"
echo ""
echo ""

# Issue 2: Get Interests - Check if it's POST or GET (needs auth)
echo "2️⃣  Testing Get Interests - Need Auth Token First"
echo "----------------------------------------------------------------------"

# First get a token via guest login
GUEST=$(curl -s -X POST "$BASE/login/guest/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: debug-interest-$TS" \
  -H "x-app-mode: prod" \
  -d '{"lat": "28.6139", "long": "77.2090"}')

TOKEN=$(echo "$GUEST" | jq -r '.tokens.access // empty')
echo "Got token: ${TOKEN:0:20}..."

if [ ! -z "$TOKEN" ]; then
  echo ""
  echo "GET /get-interests/ (with auth):"
  curl -s -X GET "$BASE/get-interests/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -H "x-device-id: debug-interest-$TS" \
    -H "x-app-mode: prod" | jq . || echo "$?"
  
  echo ""
  echo "POST /get-interests/ (with auth):"
  curl -s -X POST "$BASE/get-interests/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -H "x-device-id: debug-interest-$TS" \
    -H "x-app-mode: prod" \
    -d '{"lat": "28.6139", "long": "77.2090"}' | jq . || echo "$?"
fi

echo ""
echo ""

# Issue 3: Signup with prod debug=false - Check what happens
echo "3️⃣  Testing Signup PROD debug=false (Email Issue)"
echo "----------------------------------------------------------------------"
EMAIL_TEST="prodtest_debug_${TS}@example.com"

echo "Sending signup request..."
RESP=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE/auth/signup/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: signup-debug-$TS" \
  -H "x-app-mode: prod" \
  -d '{
    "email_id": "'"$EMAIL_TEST"'",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": [1],
    "debug": false
  }')

HTTP_CODE=$(echo "$RESP" | grep "HTTP_CODE:" | cut -d: -f2)
BODY=$(echo "$RESP" | sed '/HTTP_CODE:/d')

echo "HTTP Status: $HTTP_CODE"
echo "Response Body:"
echo "$BODY" | jq . 2>/dev/null || echo "$BODY"
echo ""
echo ""

# Issue 4: Login field name issue
echo "4️⃣  Testing Login - Checking Field Names"
echo "----------------------------------------------------------------------"

# Create user first via staging
EMAIL_LOGIN="login_test_${TS}@example.com"
echo "Creating user via staging..."
SIGNUP_LOGIN=$(curl -s -X POST "$BASE/auth/signup/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: login-test-$TS" \
  -H "x-app-mode: staging" \
  -d '{
    "email_id": "'"$EMAIL_LOGIN"'",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": [1],
    "debug": false
  }')

echo "$SIGNUP_LOGIN" | jq .

# Verify OTP
echo ""
echo "Verifying OTP..."
VERIFY_LOGIN=$(curl -s -X POST "$BASE/auth/verify-otp/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: login-verify-$TS" \
  -H "x-app-mode: staging" \
  -d '{
    "identifier": "'"$EMAIL_LOGIN"'",
    "entered_otp": "123456"
  }')

echo "$VERIFY_LOGIN" | jq .

# Try login with different field names
echo ""
echo "Login attempt with 'identifier' field:"
curl -s -X POST "$BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: login-attempt-$TS" \
  -H "x-app-mode: prod" \
  -d '{
    "identifier": "'"$EMAIL_LOGIN"'",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090"
  }' | jq . || echo "Failed"

echo ""
echo "Login attempt with 'email_id' field:"
LOGIN_RESP=$(curl -s -X POST "$BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: login-attempt2-$TS" \
  -H "x-app-mode: prod" \
  -d '{
    "email_id": "'"$EMAIL_LOGIN"'",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090"
  }')

echo "$LOGIN_RESP" | jq . || echo "$LOGIN_RESP"

LOGIN_TOKEN=$(echo "$LOGIN_RESP" | jq -r '.tokens.access // empty')

echo ""
echo ""

# Issue 5: Save Interests - Check interest IDs
if [ ! -z "$LOGIN_TOKEN" ]; then
  echo "5️⃣  Testing Save Interests - Checking Valid Interest IDs"
  echo "----------------------------------------------------------------------"
  
  echo "Trying with interest ID: 1"
  curl -s -X POST "$BASE/user/save-interests/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $LOGIN_TOKEN" \
    -H "x-device-id: interest-test-$TS" \
    -H "x-app-mode: prod" \
    -d '{"interests": [1]}' | jq . || echo "Failed"
  
  echo ""
  echo "Trying with interest IDs: [1, 2, 3]"
  curl -s -X POST "$BASE/user/save-interests/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $LOGIN_TOKEN" \
    -H "x-device-id: interest-test2-$TS" \
    -H "x-app-mode: prod" \
    -d '{"interests": [1, 2, 3]}' | jq . || echo "Failed"
  
  echo ""
  echo "Trying with interest IDs: [\"tech\", \"sports\"]"
  curl -s -X POST "$BASE/user/save-interests/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $LOGIN_TOKEN" \
    -H "x-device-id: interest-test3-$TS" \
    -H "x-app-mode: prod" \
    -d '{"interests": ["tech", "sports"]}' | jq . || echo "Failed"
fi

echo ""
echo ""
echo "======================================================================"
echo "🔍 DEBUGGING COMPLETE"
echo "======================================================================"
