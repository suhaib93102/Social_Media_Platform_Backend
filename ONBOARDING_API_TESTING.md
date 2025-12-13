# 🚀 Pinmate Onboarding API - Testing Guide

## ✅ **All Features Implemented & Tested**

---

## 📋 **New Features Added**

### 1. **OTP Verification for Signup** ✅
- OTP generation (6-digit code)
- Email/SMS sending (console logging for development)
- 10-minute OTP expiration
- Debug mode bypass

### 2. **Save Interests API** ✅
- Update user interests after account creation
- JWT authentication required

### 3. **Address Details in Profile** ✅
- Added `address_details` field to user profile
- Supports full address storage

### 4. **Debug Mode Support** ✅
- Header: `Is-Debug: true` to bypass OTP verification
- Instant account creation in debug mode

---

## 🔐 **API Endpoints**

### **1. Signup with OTP**
```bash
POST /auth/signup/
Headers: 
  Content-Type: application/json
  Is-Debug: false  # or true for debug mode

Request:
{
  "email_id": "user@example.com",
  "password": "Test@1234",
  "lat": "28.613939",
  "long": "77.209021",
  "interests": ["technology", "sports"]
}

Response (Non-Debug):
{
  "show_otp": true,
  "message": "OTP sent successfully. Please verify to complete signup.",
  "identifier": "user@example.com"
}

Response (Debug Mode):
{
  "show_otp": false,
  "message": "User created successfully (debug mode)",
  "user": {
    "userId": "user",
    "name": null,
    "email": "user@example.com"
  },
  "tokens": {
    "refresh": "...",
    "access": "..."
  }
}
```

**Test Command:**
```bash
# Non-Debug Mode
curl -X POST http://127.0.0.1:8000/auth/signup/ \
  -H "Content-Type: application/json" \
  -d '{"email_id": "test@example.com", "password": "Test@1234", "lat": "28.613939", "long": "77.209021", "interests": ["tech"]}'

# Debug Mode (Skip OTP)
curl -X POST http://127.0.0.1:8000/auth/signup/ \
  -H "Content-Type: application/json" \
  -H "Is-Debug: true" \
  -d '{"email_id": "debug@example.com", "password": "Test@1234", "lat": "28.613939", "long": "77.209021", "interests": ["tech"]}'
```

---

### **2. Verify OTP**
```bash
POST /auth/verify-otp/

Request:
{
  "identifier": "user@example.com",
  "entered_otp": "123456"
}

Response:
{
  "message": "User created successfully",
  "user": {
    "userId": "user",
    "name": null,
    "email": "user@example.com"
  },
  "tokens": {
    "refresh": "eyJhbGci...",
    "access": "eyJhbGci..."
  },
  "location_details": {
    "pincode": "110004",
    "city": "New Delhi",
    "state": "Unknown",
    "country": "India"
  }
}
```

**Test Command:**
```bash
curl -X POST http://127.0.0.1:8000/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "test@example.com", "entered_otp": "123456"}'
```

**Get OTP from Database (for testing):**
```bash
python manage.py shell -c "from api.models import OTPVerification; otp = OTPVerification.objects.filter(identifier='test@example.com').latest('created_at'); print(f'OTP: {otp.otp_code}')"
```

---

### **3. Save Interests**
```bash
POST /save-interests/
Headers:
  Authorization: Bearer <access_token>

Request:
{
  "interests": ["tech", "sports", "entertainment"]
}

Response:
{
  "message": "Interests added",
  "interests": ["tech", "sports", "entertainment"]
}
```

**Test Command:**
```bash
curl -X POST http://127.0.0.1:8000/save-interests/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"interests": ["tech", "sports", "entertainment", "music"]}'
```

---

### **4. Setup Profile (with Address)**
```bash
POST /setup-profile/
Headers:
  Authorization: Bearer <access_token>

Request:
{
  "name": "John Doe",
  "bio": "Software Developer",
  "gender": "Male",
  "age": 25,
  "image_url": "https://example.com/photo.jpg",
  "additional_pincodes": ["560001", "560002"],
  "address_details": "123 Main Street, Apartment 4B, New Delhi"
}

Response:
{
  "message": "Profile Details saved successfully."
}
```

**Test Command:**
```bash
curl -X POST http://127.0.0.1:8000/setup-profile/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Test User",
    "bio": "Software Developer",
    "gender": "Male",
    "age": 25,
    "image_url": "https://example.com/photo.jpg",
    "additional_pincodes": ["560001"],
    "address_details": "123 Main Street, New Delhi"
  }'
```

---

### **5. Guest Login**
```bash
POST /login/guest/

Request:
{
  "interests": ["Art", "Travel", "Food", "Technology"],
  "lat": "28.613939",
  "long": "77.209021"
}

Response:
{
  "message": "Guest user registered successfully",
  "user": {
    "is_guest": true
  },
  "tokens": {
    "refresh": "eyJhbGci...",
    "access": "eyJhbGci..."
  }
}
```

**Test Command:**
```bash
curl -X POST http://127.0.0.1:8000/login/guest/ \
  -H "Content-Type: application/json" \
  -d '{"interests": ["Art", "Travel", "Food"], "lat": "28.613939", "long": "77.209021"}'
```

---

### **6. Get Feed (with Interests)**
```bash
POST /get-feed/
Headers:
  Authorization: Bearer <access_token>

Request:
{
  "lat": "28.613939",
  "long": "77.209021"
}

Response:
{
  "feed": [
    {
      "id": "...",
      "type": "interest_post",
      "interest": "Technology",
      "title": "...",
      "content": "...",
      "location": {...},
      "engagement": {...}
    }
  ],
  "user_interests": ["Art", "Travel", "Food"],
  "is_guest": true
}
```

**Test Command:**
```bash
curl -X POST http://127.0.0.1:8000/get-feed/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"lat": "28.613939", "long": "77.209021"}'
```

---

## 🧪 **Complete Test Flow**

### **Scenario 1: Normal User Signup with OTP**
```bash
# Step 1: Signup (generates OTP)
curl -X POST http://127.0.0.1:8000/auth/signup/ \
  -H "Content-Type: application/json" \
  -d '{"email_id": "newuser@example.com", "password": "Test@1234", "lat": "28.613939", "long": "77.209021", "interests": ["tech"]}'

# Step 2: Get OTP from database
python manage.py shell -c "from api.models import OTPVerification; otp = OTPVerification.objects.filter(identifier='newuser@example.com').latest('created_at'); print(f'OTP: {otp.otp_code}')"

# Step 3: Verify OTP
curl -X POST http://127.0.0.1:8000/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "newuser@example.com", "entered_otp": "YOUR_OTP_HERE"}'

# Step 4: Save the access token from response
TOKEN="<access_token_from_response>"

# Step 5: Update interests
curl -X POST http://127.0.0.1:8000/save-interests/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"interests": ["tech", "sports", "music"]}'

# Step 6: Setup profile with address
curl -X POST http://127.0.0.1:8000/setup-profile/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "John Doe", "bio": "Developer", "address_details": "123 Main St"}'

# Step 7: Get personalized feed
curl -X POST http://127.0.0.1:8000/get-feed/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"lat": "28.613939", "long": "77.209021"}'
```

---

### **Scenario 2: Debug Mode Signup (Skip OTP)**
```bash
# Step 1: Signup with debug mode
curl -X POST http://127.0.0.1:8000/auth/signup/ \
  -H "Content-Type: application/json" \
  -H "Is-Debug: true" \
  -d '{"email_id": "debuguser@example.com", "password": "Test@1234", "lat": "28.613939", "long": "77.209021", "interests": ["tech"]}'

# Response includes tokens immediately - no OTP needed!
# Continue with save-interests and setup-profile as above
```

---

### **Scenario 3: Guest User**
```bash
# Step 1: Create guest account
curl -X POST http://127.0.0.1:8000/login/guest/ \
  -H "Content-Type: application/json" \
  -d '{"interests": ["Art", "Travel"], "lat": "28.613939", "long": "77.209021"}'

# Step 2: Save the access token
GUEST_TOKEN="<access_token_from_response>"

# Step 3: Get interest-based feed
curl -X POST http://127.0.0.1:8000/get-feed/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GUEST_TOKEN" \
  -d '{"lat": "28.613939", "long": "77.209021"}'
```

---

## ✅ **Test Results**

All endpoints tested successfully on **December 13, 2025**:

| Endpoint | Status | Notes |
|----------|--------|-------|
| `/auth/signup/` (OTP) | ✅ Pass | OTP generated, stored in DB |
| `/auth/signup/` (Debug) | ✅ Pass | Bypasses OTP, instant account |
| `/auth/verify-otp/` | ✅ Pass | Creates user after OTP verification |
| `/save-interests/` | ✅ Pass | Updates user interests with JWT auth |
| `/setup-profile/` | ✅ Pass | Saves address_details field |
| `/login/guest/` | ✅ Pass | Creates guest with JWT tokens |
| `/get-feed/` | ✅ Pass | Returns interest-based feed |

---

## 🔧 **Database Models Added**

### **OTPVerification**
```python
- identifier: email/phone (indexed)
- otp_code: 6-digit code
- created_at: timestamp
- expires_at: 10 minutes from creation
- is_verified: boolean flag
```

### **PendingSignup**
```python
- identifier: email/phone (unique)
- email, phone_number, password (hashed)
- latitude, longitude
- interests (JSON array)
- location details (pincode, city, state, country)
- created_at: timestamp
```

### **UserProfile (Updated)**
```python
+ address_details: TextField (nullable)
```

---

## 🌟 **Features Summary**

### ✅ **Completed Features:**
1. **OTP Verification System**
   - 6-digit OTP generation
   - Email/SMS sending (console logging for dev)
   - 10-minute expiration
   - Pending signup storage

2. **Debug Mode**
   - Header: `Is-Debug: true`
   - Bypasses OTP verification
   - Instant account creation

3. **Save Interests API**
   - JWT authenticated endpoint
   - Updates user interests array
   - Works for both guest and regular users

4. **Address Support**
   - New `address_details` field in profile
   - Stored during profile setup
   - Full address string support

5. **Guest User Flow**
   - Generates JWT tokens
   - Interest-based feed
   - Location-aware content

6. **Interest-Based Feed**
   - Personalized content based on user interests
   - Guest user welcome message
   - Location-aware posts
   - Engagement metrics

---

## 🚀 **Production Deployment Notes**

### **Email/SMS Integration Needed:**
Currently OTPs are logged to console. For production:

1. **Email Service:** Integrate SendGrid, AWS SES, or similar
   - Update `send_otp_email()` in [auth_views.py](auth_views.py)
   
2. **SMS Service:** Integrate Twilio, AWS SNS, or similar
   - Update `send_otp_sms()` in [auth_views.py](auth_views.py)

### **Security Recommendations:**
- Rate limiting on OTP generation (prevent spam)
- Monitor OTP verification attempts
- Clear expired OTPs from database (scheduled task)
- Secure headers validation
- HTTPS only in production

---

## 📚 **Related Documentation**
- [API Deployment Guide](PINMATE_API_DEPLOYED.md)
- [Implementation Summary](FINAL_IMPLEMENTATION_SUMMARY.md)
- [Postman Testing Guide](POSTMAN_TESTING_GUIDE.md)

---

**🎉 All onboarding features implemented and tested successfully!**
