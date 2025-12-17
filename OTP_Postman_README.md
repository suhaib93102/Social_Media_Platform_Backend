# OTP Testing - Postman Collection & Curl Commands

## 📋 Overview
This collection provides comprehensive testing for all 4 OTP mode combinations:
- **PROD + debug=false**: Real OTP with email sending
- **PROD + debug=true**: Skip OTP (immediate user creation)
- **STAGING + debug=false**: Default OTP "123456" (no email)
- **STAGING + debug=true**: Skip OTP (immediate user creation)

## 🚀 How to Use

### Option 1: Postman Collection (Recommended)
1. **Import the collection**: Open Postman → Import → Select `OTP_Postman_Collection.json`
2. **Set base URL**: Update `{{base_url}}` variable to your server URL (default: `http://127.0.0.1:8000`)
3. **Run tests**: Execute each request in order - the collection includes automated tests

### Option 2: Curl Commands (Manual Testing)

#### TEST 1: PROD + debug=false (Real OTP, Email Sent)
```bash
# Signup request
curl -X POST http://127.0.0.1:8000/auth/signup/ \
  -H "Content-Type: application/json" \
  -H "x-app-mode: prod" \
  -H "x-device-id: postman-test1-prod-nodebug" \
  -d '{
    "email_id": "prod_nodebug_curl@example.com",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": [1],
    "debug": false
  }'

# Expected response: {"show_otp": true, "message": "OTP sent successfully", "identifier": "..."}

# Then verify OTP (replace OTP_VALUE with actual OTP from email/database)
curl -X POST http://127.0.0.1:8000/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -H "x-app-mode: prod" \
  -H "x-device-id: postman-test1-verify-prod-nodebug" \
  -d '{
    "identifier": "prod_nodebug_curl@example.com",
    "entered_otp": "OTP_VALUE"
  }'
```

#### TEST 2: PROD + debug=true (Skip OTP)
```bash
curl -X POST http://127.0.0.1:8000/auth/signup/ \
  -H "Content-Type: application/json" \
  -H "x-app-mode: prod" \
  -H "x-device-id: postman-test2-prod-debug" \
  -d '{
    "email_id": "prod_debug_curl@example.com",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": [1],
    "debug": true
  }'

# Expected: Immediate user creation with tokens
```

#### TEST 3: STAGING + debug=false (Default OTP 123456)
```bash
# Signup request
curl -X POST http://127.0.0.1:8000/auth/signup/ \
  -H "Content-Type: application/json" \
  -H "x-app-mode: staging" \
  -H "x-device-id: postman-test3-staging-nodebug" \
  -d '{
    "email_id": "staging_nodebug_curl@example.com",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": [1],
    "debug": false
  }'

# Expected response: {"show_otp": true, "message": "OTP generated (staging mode)", "identifier": "..."}

# Verify with default OTP
curl -X POST http://127.0.0.1:8000/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -H "x-app-mode: staging" \
  -H "x-device-id: postman-test3-verify-staging-nodebug" \
  -d '{
    "identifier": "staging_nodebug_curl@example.com",
    "entered_otp": "123456"
  }'
```

#### TEST 4: STAGING + debug=true (Skip OTP)
```bash
curl -X POST http://127.0.0.1:8000/auth/signup/ \
  -H "Content-Type: application/json" \
  -H "x-app-mode: staging" \
  -H "x-device-id: postman-test4-staging-debug" \
  -d '{
    "email_id": "staging_debug_curl@example.com",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": [1],
    "debug": true
  }'

# Expected: Immediate user creation with tokens
```

## 📊 Expected Behaviors

| Mode | debug | show_otp | Email Sent | OTP Value | User Creation |
|------|-------|----------|------------|-----------|----------------|
| prod | false | true     | ✅ Yes     | Random 6-digit | After verification |
| prod | true  | false    | ❌ No      | N/A       | Immediate |
| staging | false | true     | ❌ No      | "123456"  | After verification |
| staging | true  | false    | ❌ No      | N/A       | Immediate |

## 🔧 Setup Requirements

1. **Django server running** on the specified URL
2. **Gmail SMTP configured** (for prod mode with debug=false)
3. **Database connection** for OTP storage
4. **Environment variables** set in `.env` file

## 🧪 Automated Testing

The Postman collection includes automated tests that verify:
- Correct HTTP status codes
- Proper `show_otp` values
- Expected response messages
- Presence of required fields (tokens, user data, etc.)

## 📝 Notes

- Use unique email addresses for each test to avoid conflicts
- For production testing, ensure Gmail App Password is configured
- Check server logs for email sending attempts
- OTP codes expire after 5 minutes
- Debug mode bypasses OTP for development/testing purposes