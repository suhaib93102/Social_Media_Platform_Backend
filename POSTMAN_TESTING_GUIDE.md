# 📋 **PINMATE API - ONE-BY-ONE FEATURE TESTING**

## 🎯 **Overview**
This guide provides systematic one-by-one testing for each implemented feature. Test each feature individually to ensure proper implementation.

---

## 📦 **Prerequisites**

### 1. **Start Django Server**
```bash
cd /Users/vishaljha/backend
export NODE_ENV=development  # For debug testing
python manage.py runserver
```

### 2. **Postman Environment Setup**
Create environment variables:
- `base_url`: `http://127.0.0.1:8000`
- `device_id`: `test-device-12345`
- `access_token`: `` (leave empty)
- `refresh_token`: `` (leave empty)

---

## 🧪 **FEATURE 1: HEADER ACCEPTANCE IN ALL APIs**

### **Test 1.1: Mandatory x-device-id**
```
Method: POST
URL: {{base_url}}/app-init/
Headers:
  Content-Type: application/json
  x-device-id: {{device_id}}

Body: (empty)
```

**Expected:** ✅ 201 Created (guest user created)
```json
{
  "message": "Guest user created successfully",
  "user_role": "guest",
  "tokens": {...}
}
```

### **Test 1.2: Missing x-device-id (Should Fail)**
```
Method: POST
URL: {{base_url}}/app-init/
Headers:
  Content-Type: application/json

Body: (empty)
```

**Expected:** ❌ 400 Bad Request
```json
{
  "error": "x-device-id header is required"
}
```

### **Test 1.3: Optional x-app-mode**
```
Method: POST
URL: {{base_url}}/app-init/
Headers:
  Content-Type: application/json
  x-device-id: {{device_id}}
  x-app-mode: debug

Body: (empty)
```

**Expected:** ✅ Works with or without x-app-mode

### **Test 1.4: Optional Authorization**
```
Method: POST
URL: {{base_url}}/app-init/
Headers:
  Content-Type: application/json
  x-device-id: {{device_id}}
  Authorization: Bearer some-token

Body: (empty)
```

**Expected:** ✅ Works with or without Authorization header

---

## 🧪 **FEATURE 2: GUEST AUTO ENTRY**

### **Test 2.1: First API Hit - No Auth Token**
```
Method: POST
URL: {{base_url}}/app-init/
Headers:
  Content-Type: application/json
  x-device-id: guest-device-001

Body: (empty)
```

**Expected:** ✅ 201 Created - New guest user
```json
{
  "message": "Guest user created successfully",
  "user_role": "guest",
  "tokens": {
    "refresh": "...",
    "access": "..."
  }
}
```

### **Test 2.2: Same Device ID - Find Existing Guest**
```
Method: POST
URL: {{base_url}}/app-init/
Headers:
  Content-Type: application/json
  x-device-id: guest-device-001

Body: (empty)
```

**Expected:** ✅ 200 OK - Existing guest user found
```json
{
  "message": "Guest user found",
  "user_role": "guest",
  "tokens": {
    "refresh": "...",
    "access": "..."
  }
}
```

### **Test 2.3: Different Device ID - New Guest**
```
Method: POST
URL: {{base_url}}/app-init/
Headers:
  Content-Type: application/json
  x-device-id: guest-device-002

Body: (empty)
```

**Expected:** ✅ 201 Created - Different guest user

---

## 🧪 **FEATURE 3: OTP HANDLING (DEBUG VS RELEASE)**

### **Test 3.1: Debug Mode - No SMS/Email**
```bash
export NODE_ENV=development
```
```
Method: POST
URL: {{base_url}}/auth/signup/
Headers:
  Content-Type: application/json
  x-device-id: {{device_id}}
  x-app-mode: debug

Body:
{
  "email_id": "debug@example.com",
  "password": "TestPass123",
  "long": "77.5946",
  "lat": "12.9716",
  "interests": ["technology"]
}
```

**Expected:** ✅ 200 OK - No OTP sent
```json
{
  "message": "User created successfully",
  "show_otp": false,
  "location_details": {...}
}
```

### **Test 3.2: Production Mode - Real OTP**
```bash
export NODE_ENV=production
```
```
Method: POST
URL: {{base_url}}/auth/signup/
Headers:
  Content-Type: application/json
  x-device-id: {{device_id}}
  x-app-mode: production

Body:
{
  "email_id": "prod@example.com",
  "password": "TestPass123",
  "long": "77.5946",
  "lat": "12.9716",
  "interests": ["technology"]
}
```

**Expected:** ✅ 200 OK - Real OTP sent
```json
{
  "message": "OTP sent successfully",
  "show_otp": true
}
```

---

## 🧪 **FEATURE 4: OTP VERIFY LOGIC**

### **Test 4.1: Debug Mode - Accept Fixed OTP**
```bash
export NODE_ENV=development
```
```
Method: POST
URL: {{base_url}}/auth/verify-otp/
Headers:
  Content-Type: application/json
  x-device-id: {{device_id}}
  x-app-mode: debug

Body:
{
  "email_id": "debug@example.com",
  "otp": "123456"
}
```

**Expected:** ✅ 200 OK
```json
{
  "message": "OTP verified successfully",
  "user": {...}
}
```

### **Test 4.2: Production Mode - Reject Fixed OTP**
```bash
export NODE_ENV=production
```
```
Method: POST
URL: {{base_url}}/auth/verify-otp/
Headers:
  Content-Type: application/json
  x-device-id: {{device_id}}
  x-app-mode: production

Body:
{
  "email_id": "prod@example.com",
  "otp": "123456"
}
```

**Expected:** ❌ 400 Bad Request
```json
{
  "error": "Invalid OTP for production mode"
}
```

---

## 🧪 **FEATURE 5: GUEST → USER UPGRADE**

### **Test 5.1: Create Guest User**
```
Method: POST
URL: {{base_url}}/app-init/
Headers:
  Content-Type: application/json
  x-device-id: upgrade-device-001

Body: (empty)
```

**Expected:** ✅ Guest created, note the user ID

### **Test 5.2: Upgrade Guest to User**
```bash
export NODE_ENV=development
```
```
Method: POST
URL: {{base_url}}/auth/signup/
Headers:
  Content-Type: application/json
  x-device-id: upgrade-device-001
  x-app-mode: debug

Body:
{
  "email_id": "upgrade@example.com",
  "password": "UpgradePass123",
  "long": "77.5946",
  "lat": "12.9716",
  "interests": ["technology"]
}
```

**Expected:** ✅ Same user record updated
```json
{
  "message": "User created successfully",
  "user": {
    "userId": "upgrade"  // Same as guest user ID
  }
}
```

### **Test 5.3: Verify Upgrade - Check User Role**
```
Method: POST
URL: {{base_url}}/app-init/
Headers:
  Content-Type: application/json
  x-device-id: upgrade-device-001

Body: (empty)
```

**Expected:** ✅ Now returns "user" role
```json
{
  "message": "User found",
  "user_role": "user",  // Changed from "guest"
  "tokens": {...}
}
```

---

## 🧪 **FEATURE 6: AUTH MIDDLEWARE**

### **Test 6.1: Token Exists → Logged-in User**
```
Method: POST
URL: {{base_url}}/get-interests/
Headers:
  Content-Type: application/json
  x-device-id: {{device_id}}
  Authorization: Bearer {{access_token}}

Body:
{
  "long": "77.5946",
  "lat": "12.9716"
}
```

**Expected:** ✅ 200 OK - Authenticated user

### **Test 6.2: No Token + Device ID → Guest User**
```
Method: POST
URL: {{base_url}}/get-interests/
Headers:
  Content-Type: application/json
  x-device-id: guest-device-001

Body:
{
  "long": "77.5946",
  "lat": "12.9716"
}
```

**Expected:** ❌ 401 Unauthorized (if endpoint requires auth)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### **Test 6.3: No Token + No Device ID → Reject**
```
Method: POST
URL: {{base_url}}/get-interests/
Headers:
  Content-Type: application/json

Body:
{
  "long": "77.5946",
  "lat": "12.9716"
}
```

**Expected:** ❌ 400 Bad Request
```json
{
  "error": "x-device-id header is required"
}
```

---

## 🧪 **FEATURE 7: SECURITY MEASURES**

### **Test 7.1: Reject Missing Device ID**
```
Method: POST
URL: {{base_url}}/auth/signup/
Headers:
  Content-Type: application/json
  x-app-mode: debug

Body:
{
  "email_id": "test@example.com",
  "password": "TestPass123",
  "long": "77.5946",
  "lat": "12.9716",
  "interests": ["technology"]
}
```

**Expected:** ❌ 400 Bad Request
```json
{
  "error": "x-device-id header is required"
}
```

### **Test 7.2: Block OTP Bypass in Production**
```bash
export NODE_ENV=production
```
```
Method: POST
URL: {{base_url}}/auth/verify-otp/
Headers:
  Content-Type: application/json
  x-device-id: {{device_id}}
  x-app-mode: debug  # Even if debug mode requested

Body:
{
  "email_id": "prod@example.com",
  "otp": "123456"
}
```

**Expected:** ❌ 400 Bad Request (NODE_ENV takes precedence)
```json
{
  "error": "Invalid OTP for production mode"
}
```

### **Test 7.3: All Endpoints Require Device ID**
Test any endpoint without `x-device-id`:
- `/auth/signup/`
- `/auth/verify-otp/`
- `/get-interests/`
- `/app-init/`

**Expected:** ❌ All should return 400 Bad Request

---

## 📊 **TESTING CHECKLIST**

### **Feature 1: Header Acceptance**
- [ ] x-device-id mandatory validation
- [ ] x-app-mode optional
- [ ] Authorization optional
- [ ] All APIs accept these headers

### **Feature 2: Guest Auto Entry**
- [ ] First hit creates guest user
- [ ] Same device finds existing guest
- [ ] Returns user_role: "guest"
- [ ] Different devices create different guests

### **Feature 3: OTP Handling**
- [ ] Debug mode: no SMS/email, show_otp: false
- [ ] Production mode: real OTP sent, show_otp: true
- [ ] NODE_ENV controls behavior

### **Feature 4: OTP Verify Logic**
- [ ] Debug accepts "123456"
- [ ] Production rejects "123456"
- [ ] Production verifies real OTP

### **Feature 5: Guest → User Upgrade**
- [ ] Same user record updated
- [ ] No duplicate user created
- [ ] Role changes from guest to user
- [ ] Device ID link preserved

### **Feature 6: Auth Middleware**
- [ ] Token → logged-in user
- [ ] No token + device ID → guest user
- [ ] No token + no device ID → rejected

### **Feature 7: Security**
- [ ] All requests rejected without x-device-id
- [ ] Production blocks OTP bypass regardless of x-app-mode
- [ ] NODE_ENV takes precedence over x-app-mode

---

## 🎯 **SUCCESS CRITERIA**

✅ **All 7 features implemented and tested individually**  
✅ **Each test case produces expected results**  
✅ **Security measures prevent unauthorized access**  
✅ **Debug/production modes work correctly**  
✅ **Guest-to-user upgrade preserves data integrity**  

---

## 📞 **Quick Test Commands**

```bash
# Test header validation
curl -X POST http://127.0.0.1:8000/app-init/ \
  -H "Content-Type: application/json"

# Should fail: {"error": "x-device-id header is required"}

curl -X POST http://127.0.0.1:8000/app-init/ \
  -H "Content-Type: application/json" \
  -H "x-device-id: test-device-123"

# Should succeed: {"message": "Guest user created successfully", "user_role": "guest"}
```

---

**🎉 Test each feature one-by-one to ensure complete implementation!**