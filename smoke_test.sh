#!/usr/bin/env bash
# Smoke test script for the Social Media Platform API

DEFAULT_BASE_URL="https://social-media-platform-backend-4oz4.onrender.com"
BASE_URL="${BASE_URL:-$DEFAULT_BASE_URL}"

USER_ID="smokeuser001"
USER_EMAIL="smokeuser001@example.com"

set -euo pipefail

echo "Using BASE_URL: $BASE_URL"

NEW_USER_PAYLOAD=$(cat <<EOF
{
  "userId": "${USER_ID}",
  "name": "Smoke User",
  "email": "${USER_EMAIL}"
}
EOF
)

echo "\n1) Try to create or detect user POST /users/"
curl -s -X POST "$BASE_URL/users/" -H "Content-Type: application/json" -d "$NEW_USER_PAYLOAD" | jq || true

echo "\n2) GET created (or existing) user by id GET /users/${USER_ID}/"
GET_USER_URL="${BASE_URL}/users/${USER_ID}/"
curl -s "$GET_USER_URL" | jq || true

echo "\n3) INVALID LOGIN (should be 404)"
INVALID_ID="this_user_does_not_exist_123"
HTTP_STATUS_INVALID=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/users/${INVALID_ID}/" || echo "000")
if [[ "$HTTP_STATUS_INVALID" == "404" ]]; then
  echo "✅ 404 Not Found for invalid user"
else
  echo "⚠️  Received HTTP status: ${HTTP_STATUS_INVALID}"
fi

echo "\n4) DUPLICATE SIGNUP (should be rejected)"
DUP_PAYLOAD=$(cat <<EOF
{
  "userId": "${USER_ID}_dup",
  "name": "Smoke User Dup",
  "email": "${USER_EMAIL}",
  "gender": "male",
  "age": 25
}
EOF
)
RESPONSE_DUP=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/users/" -H "Content-Type: application/json" -d "$DUP_PAYLOAD" || true)
HTTP_STATUS_DUP=$(printf '%s' "$RESPONSE_DUP" | tail -n1)
RESPONSE_BODY_DUP=$(printf '%s' "$RESPONSE_DUP" | sed '$d')
if [[ "$HTTP_STATUS_DUP" == "400" ]]; then
  echo "✅ Duplicate signup correctly rejected (400)"
else
  echo "⚠️  Duplicate signup returned status: ${HTTP_STATUS_DUP}"
  [[ -n "$RESPONSE_BODY_DUP" ]] && echo "Response body: $RESPONSE_BODY_DUP"
fi

echo "\nSMOKE AUTH TESTS COMPLETE"