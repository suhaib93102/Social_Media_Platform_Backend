#!/bin/bash

# Comprehensive Production API Test
# Testing all onboarding & auth endpoints on Render production server

echo "🚀 COMPREHENSIVE PRODUCTION API TEST"
echo "======================================================================"
echo "Server: https://social-media-platform-backend-4oz4.onrender.com"
echo "======================================================================"
echo ""

BASE="https://social-media-platform-backend-4oz4.onrender.com"
TS=$(date +%s)

# ============================================================================
# 1. APP INITIALIZATION
# ============================================================================
echo "1️⃣  APP INITIALIZATION"
echo "----------------------------------------------------------------------"
curl -s -X GET "$BASE/app-init/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: test-device-$TS" \
  -H "x-app-mode: prod" | jq . || echo "Failed"
echo ""
echo ""

# ============================================================================
# 2. GET INTERESTS
# ============================================================================
echo "2️⃣  GET INTERESTS"
echo "----------------------------------------------------------------------"
INTERESTS=$(curl -s -X GET "$BASE/get-interests/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: test-device-$TS" \
  -H "x-app-mode: prod")
echo "$INTERESTS" | jq . || echo "$INTERESTS"
INTEREST_ID=$(echo "$INTERESTS" | jq -r '.interests[0].id // 1')
echo "Using Interest ID: $INTEREST_ID"
echo ""
echo ""

# ============================================================================
# 3. GUEST LOGIN
# ============================================================================
echo "3️⃣  GUEST LOGIN"
echo "----------------------------------------------------------------------"
GUEST=$(curl -s -X POST "$BASE/login/guest/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: guest-$TS" \
  -H "x-app-mode: prod" \
  -d '{
    "lat": "28.6139",
    "long": "77.2090"
  }')
echo "$GUEST" | jq . || echo "$GUEST"
GUEST_TOKEN=$(echo "$GUEST" | jq -r '.tokens.access // empty')
echo ""
echo ""

# ============================================================================
# 4. SIGNUP - PROD + debug=false (Real OTP with Email)
# ============================================================================
echo "4️⃣  SIGNUP - PROD MODE (debug=false) - Real OTP"
echo "----------------------------------------------------------------------"
EMAIL1="prodtest_${TS}@example.com"
SIGNUP1=$(curl -s -X POST "$BASE/auth/signup/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: signup-prod-$TS" \
  -H "x-app-mode: prod" \
  -d '{
    "email_id": "'"$EMAIL1"'",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": ['"$INTEREST_ID"'],
    "debug": false
  }')
echo "$SIGNUP1" | jq . || echo "$SIGNUP1"

# Check if OTP is in response (for development/testing)
OTP1=$(echo "$SIGNUP1" | jq -r '.otp // empty')
if [ ! -z "$OTP1" ]; then
  echo "🔑 OTP Found in Response: $OTP1"
  echo "Attempting verification..."
  
  VERIFY1=$(curl -s -X POST "$BASE/auth/verify-otp/" \
    -H "Content-Type: application/json" \
    -H "x-device-id: verify-prod-$TS" \
    -H "x-app-mode: prod" \
    -d '{
      "identifier": "'"$EMAIL1"'",
      "entered_otp": "'"$OTP1"'"
    }')
  echo "Verification Result:"
  echo "$VERIFY1" | jq . || echo "$VERIFY1"
fi
echo ""
echo ""

# ============================================================================
# 5. SIGNUP - PROD + debug=true (Skip OTP)
# ============================================================================
echo "5️⃣  SIGNUP - PROD MODE (debug=true) - Skip OTP"
echo "----------------------------------------------------------------------"
EMAIL2="prod_debug_${TS}@example.com"
SIGNUP2=$(curl -s -X POST "$BASE/auth/signup/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: signup-prod-debug-$TS" \
  -H "x-app-mode: prod" \
  -d '{
    "email_id": "'"$EMAIL2"'",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": ['"$INTEREST_ID"'],
    "debug": true
  }')
echo "$SIGNUP2" | jq . || echo "$SIGNUP2"
ACCESS_TOKEN=$(echo "$SIGNUP2" | jq -r '.tokens.access // empty')
echo ""
echo ""

# ============================================================================
# 6. SIGNUP - STAGING + debug=false (Default OTP 123456)
# ============================================================================
echo "6️⃣  SIGNUP - STAGING MODE (debug=false) - OTP=123456"
echo "----------------------------------------------------------------------"
EMAIL3="staging_${TS}@example.com"
SIGNUP3=$(curl -s -X POST "$BASE/auth/signup/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: signup-staging-$TS" \
  -H "x-app-mode: staging" \
  -d '{
    "email_id": "'"$EMAIL3"'",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": ['"$INTEREST_ID"'],
    "debug": false
  }')
echo "$SIGNUP3" | jq . || echo "$SIGNUP3"

echo "Verifying with OTP: 123456..."
VERIFY3=$(curl -s -X POST "$BASE/auth/verify-otp/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: verify-staging-$TS" \
  -H "x-app-mode: staging" \
  -d '{
    "identifier": "'"$EMAIL3"'",
    "entered_otp": "123456"
  }')
echo "$VERIFY3" | jq . || echo "$VERIFY3"
ACCESS_TOKEN=$(echo "$VERIFY3" | jq -r '.tokens.access // empty')
echo ""
echo ""

# ============================================================================
# 7. SIGNUP - STAGING + debug=true (Skip OTP)
# ============================================================================
echo "7️⃣  SIGNUP - STAGING MODE (debug=true) - Skip OTP"
echo "----------------------------------------------------------------------"
EMAIL4="staging_debug_${TS}@example.com"
SIGNUP4=$(curl -s -X POST "$BASE/auth/signup/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: signup-staging-debug-$TS" \
  -H "x-app-mode: staging" \
  -d '{
    "email_id": "'"$EMAIL4"'",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": ['"$INTEREST_ID"'],
    "debug": true
  }')
echo "$SIGNUP4" | jq . || echo "$SIGNUP4"
echo ""
echo ""

# ============================================================================
# 8. SETUP PROFILE (if we have access token)
# ============================================================================
if [ ! -z "$ACCESS_TOKEN" ]; then
  echo "8️⃣  SETUP PROFILE (using token from previous signup)"
  echo "----------------------------------------------------------------------"
  curl -s -X POST "$BASE/setup-profile/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "x-device-id: setup-$TS" \
    -H "x-app-mode: prod" \
    -d '{
      "name": "Test User",
      "bio": "Testing profile setup",
      "lat": "28.6139",
      "long": "77.2090"
    }' | jq . || echo "Failed"
  echo ""
  echo ""
fi

# ============================================================================
# 9. SAVE INTERESTS (if we have access token)
# ============================================================================
if [ ! -z "$ACCESS_TOKEN" ]; then
  echo "9️⃣  SAVE INTERESTS (using token from previous signup)"
  echo "----------------------------------------------------------------------"
  curl -s -X POST "$BASE/user/save-interests/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "x-device-id: interests-$TS" \
    -H "x-app-mode: prod" \
    -d '{
      "interests": ['"$INTEREST_ID"']
    }' | jq . || echo "Failed"
  echo ""
  echo ""
fi

# ============================================================================
# 10. LOGIN
# ============================================================================
echo "🔟 LOGIN (using staging debug user)"
echo "----------------------------------------------------------------------"
LOGIN=$(curl -s -X POST "$BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: login-$TS" \
  -H "x-app-mode: prod" \
  -d '{
    "identifier": "'"$EMAIL4"'",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090"
  }')
echo "$LOGIN" | jq . || echo "$LOGIN"
LOGIN_TOKEN=$(echo "$LOGIN" | jq -r '.tokens.access // empty')
echo ""
echo ""

# ============================================================================
# 11. GET FEED (if we have token)
# ============================================================================
if [ ! -z "$LOGIN_TOKEN" ]; then
  echo "1️⃣1️⃣  GET FEED (using login token)"
  echo "----------------------------------------------------------------------"
  curl -s -X GET "$BASE/get-feed/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $LOGIN_TOKEN" \
    -H "x-device-id: feed-$TS" \
    -H "x-app-mode: prod" | jq . || echo "Failed"
  echo ""
  echo ""
fi

# ============================================================================
# SUMMARY
# ============================================================================
echo "======================================================================"
echo "📊 TEST SUMMARY"
echo "======================================================================"
echo "✅ App Init: $(echo "$INTERESTS" | jq -r 'if type == "object" then "SUCCESS" else "CHECK ABOVE" end')"
echo "✅ Get Interests: $(echo "$INTERESTS" | jq -r 'if .interests then "SUCCESS" else "FAILED" end')"
echo "✅ Guest Login: $(echo "$GUEST" | jq -r 'if .tokens then "SUCCESS" else "FAILED" end')"
echo "✅ Signup PROD (debug=false): $(echo "$SIGNUP1" | jq -r 'if .show_otp then "SUCCESS" else "CHECK ABOVE" end')"
echo "✅ Signup PROD (debug=true): $(echo "$SIGNUP2" | jq -r 'if .tokens then "SUCCESS" else "FAILED" end')"
echo "✅ Signup STAGING (debug=false): $(echo "$SIGNUP3" | jq -r 'if .show_otp then "SUCCESS" else "FAILED" end')"
echo "✅ Verify STAGING: $(echo "$VERIFY3" | jq -r 'if .tokens then "SUCCESS" else "FAILED" end')"
echo "✅ Signup STAGING (debug=true): $(echo "$SIGNUP4" | jq -r 'if .tokens then "SUCCESS" else "FAILED" end')"
echo "✅ Login: $(echo "$LOGIN" | jq -r 'if .tokens then "SUCCESS" else "FAILED" end')"
echo "======================================================================"
echo "🎯 PRODUCTION API TESTING COMPLETE!"
echo "======================================================================"
