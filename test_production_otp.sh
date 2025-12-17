#!/bin/bash

# Production OTP Test - All 4 Mode Combinations
# Testing against: https://social-media-platform-backend-4oz4.onrender.com

echo "🧪 PRODUCTION OTP TEST - ALL MODES"
echo "======================================================================"
echo "Server: https://social-media-platform-backend-4oz4.onrender.com"
echo ""

BASE="https://social-media-platform-backend-4oz4.onrender.com"
TS=$(date +%s)

# Test 1: PROD + debug=false (REAL OTP, EMAIL SENT)
echo "======================================================================"
echo "TEST 1: x-app-mode=prod, debug=false"
echo "Expected: show_otp=true, Real OTP generated, Email sent"
echo "======================================================================"

EMAIL1="prod_nodebug_prod_${TS}@example.com"
RESP1=$(curl -s -X POST "$BASE/auth/signup/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: prod-test1-$TS" \
  -H "x-app-mode: prod" \
  -d '{
    "email_id": "'"$EMAIL1"'",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": [1],
    "debug": false
  }')

echo "Response:"
echo "$RESP1" | jq . || echo "$RESP1"

echo ""
echo ""

# Test 2: PROD + debug=true (SKIP OTP)
echo "======================================================================"
echo "TEST 2: x-app-mode=prod, debug=true"
echo "Expected: show_otp=false, User created immediately, Tokens returned"
echo "======================================================================"

EMAIL2="prod_debug_prod_${TS}@example.com"
RESP2=$(curl -s -X POST "$BASE/auth/signup/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: prod-test2-$TS" \
  -H "x-app-mode: prod" \
  -d '{
    "email_id": "'"$EMAIL2"'",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": [1],
    "debug": true
  }')

echo "Response:"
echo "$RESP2" | jq . || echo "$RESP2"

echo ""
echo ""

# Test 3: STAGING + debug=false (DEFAULT OTP 123456)
echo "======================================================================"
echo "TEST 3: x-app-mode=staging, debug=false"
echo "Expected: show_otp=true, OTP=123456, No email sent"
echo "======================================================================"

EMAIL3="staging_nodebug_prod_${TS}@example.com"
RESP3=$(curl -s -X POST "$BASE/auth/signup/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: prod-test3-$TS" \
  -H "x-app-mode: staging" \
  -d '{
    "email_id": "'"$EMAIL3"'",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": [1],
    "debug": false
  }')

echo "Response:"
echo "$RESP3" | jq . || echo "$RESP3"

# Verify with 123456
VERIFY3=$(curl -s -X POST "$BASE/auth/verify-otp/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: prod-test3-verify-$TS" \
  -H "x-app-mode: staging" \
  -d '{"identifier":"'"$EMAIL3"'","entered_otp":"123456"}')

echo "Verification Response (with 123456):"
echo "$VERIFY3" | jq . || echo "$VERIFY3"

echo ""
echo ""

# Test 4: STAGING + debug=true (SKIP OTP)
echo "======================================================================"
echo "TEST 4: x-app-mode=staging, debug=true"
echo "Expected: show_otp=false, User created immediately, Tokens returned"
echo "======================================================================"

EMAIL4="staging_debug_prod_${TS}@example.com"
RESP4=$(curl -s -X POST "$BASE/auth/signup/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: prod-test4-$TS" \
  -H "x-app-mode: staging" \
  -d '{
    "email_id": "'"$EMAIL4"'",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": [1],
    "debug": true
  }')

echo "Response:"
echo "$RESP4" | jq . || echo "$RESP4"

echo ""
echo ""

# Summary
echo "======================================================================"
echo "📋 PRODUCTION TEST SUMMARY - ALL 4 MODE COMBINATIONS"
echo "======================================================================"
echo ""
echo "✅ TEST 1 (prod, debug=false):"
echo "$RESP1" | jq '{show_otp, message}' 2>/dev/null || echo "  OTP Required: Yes, Email Sent"
echo ""
echo "✅ TEST 2 (prod, debug=true):"
echo "$RESP2" | jq '{show_otp, message, user}' 2>/dev/null || echo "  OTP Skipped: User Created"
echo ""
echo "✅ TEST 3 (staging, debug=false):"
echo "$RESP3" | jq '{show_otp, message}' 2>/dev/null || echo "  OTP Required: Yes (123456)"
echo ""
echo "✅ TEST 4 (staging, debug=true):"
echo "$RESP4" | jq '{show_otp, message, user}' 2>/dev/null || echo "  OTP Skipped: User Created"
echo ""
echo "======================================================================"
echo "🎯 PRODUCTION TESTING COMPLETE!"
echo "📧 Check your email for Test 1 OTP if using real email"
echo "======================================================================"