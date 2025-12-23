#!/usr/bin/env bash
set -euo pipefail

# test_otp_matrix.sh
# Usage:
#   BASE=http://127.0.0.1:8000 ./scripts/test_otp_matrix.sh [--local]
#   BASE=https://social-media-platform-backend-4oz4.onrender.com ./scripts/test_otp_matrix.sh
#
# If --local is provided, the script will attempt to read the OTP from the local DB
# via `python manage.py shell` so it can perform a full verify with the real OTP.

BASE=${BASE:-http://127.0.0.1:8000}
LOCAL=false
if [ "${1:-}" == "--local" ]; then
  LOCAL=true
fi

which jq >/dev/null 2>&1 || { echo "Please install jq to run this script (mac: brew install jq)."; exit 1; }

run_signup() {
  local app_mode=$1
  local debug_flag=$2
  local ts=$(date +%s)
  local email="test-${app_mode}-${debug_flag}-${ts}@example.com"
  local device="device-${app_mode}-${debug_flag}-${ts}"
  printf "\n--- SIGNUP: app_mode=%s debug=%s (email=%s)\n" "$app_mode" "$debug_flag" "$email"

  if [ "$debug_flag" == "true" ]; then
    body='{"email_id":"'$email'","password":"Test123","lat":"12.9716","long":"77.5946","interests":[],"debug":true}'
  else
    body='{"email_id":"'$email'","password":"Test123","lat":"12.9716","long":"77.5946","interests":[]}'
  fi

  resp=$(curl -s -X POST "$BASE/auth/signup/" \
    -H "Content-Type: application/json" \
    -H "x-device-id: $device" \
    -H "app-mode: $app_mode" \
    -d "$body")

  echo "$resp" | jq '.'

  show_otp=$(echo "$resp" | jq -r '.show_otp // "null"')
  identifier=$(echo "$resp" | jq -r '.identifier // empty')
  access=$(echo "$resp" | jq -r '.tokens.access // empty')

  # Decide expected behavior per table (current implementation):
  # - app_mode=release & debug=true => bypass (no OTP, show_otp=false)
  # - otherwise => show_otp=true (OTP required or debug env behavior)

  if [ "$app_mode" = "release" ] && [ "$debug_flag" = "true" ]; then
    expected_show_otp="false"
  else
    expected_show_otp="true"
  fi

  if [ "$show_otp" = "$expected_show_otp" ]; then
    echo "[OK] show_otp matches expected ($expected_show_otp)"
  else
    echo "[FAIL] show_otp expected $expected_show_otp but got $show_otp"
  fi

  if [ "$show_otp" = "false" ]; then
    # Should have tokens and be a full user
    if [ -n "$access" ]; then
      echo "[OK] User created immediately; access token present"
    else
      echo "[FAIL] Expected access token but none present"
    fi
  else
    # OTP flow: test verification
    if [ -z "$identifier" ]; then
      echo "[WARN] No identifier returned; cannot test verification"
      return
    fi

    echo "Identifier: $identifier"

    # First attempt with wrong OTP (123456) - in production should be rejected; in debug env may be accepted
    echo "-> Verify with wrong OTP (123456)"
    wrong_raw=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$BASE/auth/verify-otp/" \
      -H "Content-Type: application/json" \
      -H "x-device-id: $device" \
      -H "app-mode: $app_mode" \
      -d '{"identifier":"'