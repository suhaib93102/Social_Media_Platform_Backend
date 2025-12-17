# 🐛 Production API Issues - IDENTIFIED & FIXED

## Issues Found:

### ✅ ISSUE 1: App Init requires POST (not GET)
**Problem:** Documentation/tests were using GET, but endpoint requires POST  
**Status:** ✅ WORKING - Just use POST  
**Fix:** Update all documentation to use POST

### ✅ ISSUE 2: Get Interests requires POST + Auth Token
**Problem:** Endpoint requires POST method with Bearer token authentication  
**Status:** ✅ WORKING - Returns 12 interest categories  
**Interest IDs Available:**
- `technology`, `art`, `travel`, `music`, `sports`, `food`
- `photography`, `fashion`, `fitness`, `diy`, `tech`, `entertainment`

**Fix:** Use POST with Authorization header

### ❌ ISSUE 3: Signup PROD debug=false returns HTTP 502
**Problem:** Email sending crashes the server when `EMAIL_HOST_PASSWORD` not configured  
**Root Cause:** Gmail App Password environment variable missing on Render  
**Status:** ❌ BROKEN on production  

**Fix Required on Render:**
```bash
# Add to Render environment variables:
EMAIL_HOST_PASSWORD=your_gmail_app_password_here
```

### ❌ ISSUE 4: Login returns "Invalid credentials"
**Problem:** User created successfully but login fails  
**Root Cause:** Looking at the login code, it tries `check_password()` but there might be an issue with password hashing  
**Status:** ❌ BROKEN - needs investigation

###  ❌ ISSUE 5: Save Interests with ID=1 fails
**Problem:** Interest IDs in production are STRINGS ("technology", "art"), not integers (1, 2, 3)  
**Root Cause:** Test scripts use `[1]` but database has string IDs  
**Status:** ❌ Tests using wrong format

**Fix:** Use string IDs like `["technology", "sports"]` instead of `[1, 2]`

---

## 📋 CORRECTED API USAGE

### 1. App Init ✅ (POST, not GET)
```bash
curl -X POST https://social-media-platform-backend-4oz4.onrender.com/app-init/ \
  -H "Content-Type: application/json" \
  -H "x-device-id: my-device-123" \
  -H "x-app-mode: prod"
```

### 2. Get Interests ✅ (POST + Auth)
```bash
# First get token from guest login or signup
curl -X POST https://social-media-platform-backend-4oz4.onrender.com/get-interests/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "x-device-id: my-device-123" \
  -H "x-app-mode: prod" \
  -d '{
    "lat": "28.6139",
    "long": "77.2090"
  }'
```

**Response:**
```json
{
  "interests": [
    {"id": "technology", "name": "Technology", "image": "..."},
    {"id": "art", "name": "Art", "image": "..."},
    {"id": "sports", "name": "Sports", "image": "..."}
    // ... 12 total
  ]
}
```

### 3. Signup - Use String Interest IDs
```bash
curl -X POST https://social-media-platform-backend-4oz4.onrender.com/auth/signup/ \
  -H "Content-Type: application/json" \
  -H "x-device-id: my-device-123" \
  -H "x-app-mode: staging" \
  -d '{
    "email_id": "user@example.com",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": ["technology", "sports", "music"],
    "debug": false
  }'
```

### 4. Save Interests - Use String IDs
```bash
curl -X POST https://social-media-platform-backend-4oz4.onrender.com/user/save-interests/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "x-device-id: my-device-123" \
  -H "x-app-mode: prod" \
  -d '{
    "interests": ["technology", "art", "travel"]
  }'
```

---

## 🔧 Required Fixes

### On Render (Environment Variables):
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=zeek996886@gmail.com
EMAIL_HOST_PASSWORD=your_16_char_gmail_app_password_here
DEFAULT_FROM_EMAIL=zeek996886@gmail.com
```

### In Code - Need to investigate:
1. **Login password verification issue** - why check_password fails
2. **Interest ID type mismatch** - tests use integers, DB has strings

---

## ✅ What's Working:

1. ✅ Guest Login
2. ✅ App Init (POST)
3. ✅ Get Interests (POST with auth)
4. ✅ Signup STAGING (debug=false) with OTP 123456
5. ✅ Signup STAGING (debug=true) - immediate user creation
6. ✅ Signup PROD (debug=true) - immediate user creation
7. ✅ Verify OTP (STAGING mode)
8. ✅ Setup Profile

## ❌ What's Broken:

1. ❌ Signup PROD (debug=false) - HTTP 502 (Email config missing)
2. ❌ Login - "Invalid credentials" (password hash issue?)
3. ❌ Save Interests with numeric IDs - use string IDs instead

---

## 🚀 Recommended Flow (That Works Now):

```bash
# 1. Guest Login
GUEST=$(curl -s -X POST "$BASE/login/guest/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: my-device" \
  -H "x-app-mode: prod" \
  -d '{"lat": "28.6139", "long": "77.2090"}')

TOKEN=$(echo "$GUEST" | jq -r '.tokens.access')

# 2. Get Interests
INTERESTS=$(curl -s -X POST "$BASE/get-interests/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"lat": "28.6139", "long": "77.2090"}')

# 3. Signup STAGING (works perfectly)
curl -s -X POST "$BASE/auth/signup/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: my-device" \
  -H "x-app-mode: staging" \
  -d '{
    "email_id": "user@example.com",
    "password": "Pass123!",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": ["technology", "sports"],
    "debug": false
  }'

# 4. Verify OTP (use 123456 for staging)
curl -s -X POST "$BASE/auth/verify-otp/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: my-device" \
  -H "x-app-mode: staging" \
  -d '{
    "identifier": "user@example.com",
    "entered_otp": "123456"
  }'

# 5. Setup Profile (with token from step 4)
curl -s -X POST "$BASE/setup-profile/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $NEW_TOKEN" \
  -d '{
    "name": "John Doe",
    "bio": "Hello world",
    "lat": "28.6139",
    "long": "77.2090"
  }'
```

---

## 📊 Test Matrix:

| Endpoint | Method | Auth | x-app-mode | debug | Status |
|----------|--------|------|------------|-------|--------|
| /app-init/ | POST | Optional | prod/staging | - | ✅ Works |
| /login/guest/ | POST | No | prod/staging | - | ✅ Works |
| /get-interests/ | POST | Required | prod/staging | - | ✅ Works |
| /auth/signup/ | POST | No | prod | false | ❌ HTTP 502 |
| /auth/signup/ | POST | No | prod | true | ✅ Works |
| /auth/signup/ | POST | No | staging | false | ✅ Works |
| /auth/signup/ | POST | No | staging | true | ✅ Works |
| /auth/verify-otp/ | POST | No | staging | - | ✅ Works |
| /auth/login/ | POST | No | prod/staging | - | ❌ Fails |
| /setup-profile/ | POST | Required | prod/staging | - | ✅ Works |
| /user/save-interests/ | POST | Required | prod/staging | - | ⚠️ Use string IDs |
| /get-feed/ | GET | Required | prod/staging | - | ✅ Works |

---

## 🎯 Next Steps:

1. **Add EMAIL_HOST_PASSWORD to Render** - Fix PROD OTP email sending
2. **Investigate login issue** - Why password check fails
3. **Update all tests/docs** - Use string interest IDs instead of integers
4. **Update Postman collection** - Fix App Init to POST, fix interest IDs