# Create Test User (Debug Mode - No OTP Required)
curl -X POST "http://127.0.0.1:8000/api/auth/signup/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: test-device-$(date +%s)" \
  -H "app-mode: debug" \
  -H "x-debug: true" \
  -d '{
    "email_id": "testuser@example.com",
    "password": "password123",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": ["technology", "sports"]
  }' | jq '.tokens.access'