# Pinmate API - Enhanced Header & Device Management

## ✅ Features Implemented

### 1. **Header Management (All APIs)**
- **x-device-id** (mandatory): Unique device identifier
- **x-app-mode** (optional): 'debug' or 'release' (default: 'release')
- **Authorization** (optional): Bearer token for authenticated requests

### 2. **Guest Auto-Entry**
- **Endpoint**: `POST /app-init/`
- **Headers**: x-device-id (mandatory), x-app-mode (optional)
- **Behavior**:
  - If no auth token but x-device-id provided → auto-create/find guest user
  - Return `user_role: 'guest'` with tokens
  - Subsequent calls with same device-id find existing guest

### 3. **OTP Handling (Debug vs Release)**

**Debug Mode** (x-app-mode=debug):
- Fixed OTP: `123456`
- No SMS/Email sent
- Immediate OTP acceptance

**Release Mode** (x-app-mode=release):
- Generated OTP sent via SMS/Email
- Proper OTP verification required
- Expiration validation enabled

### 4. **Guest → User Upgrade**
- After OTP verification, if guest exists with same device-id:
  - Update guest record (don't create new)
  - Convert is_guest: false
  - Preserve device-id link

## 🧪 Test Results

### Test 1: Guest Auto-Entry (App Init)
```bash
# Request
POST /app-init/
Headers: x-device-id: device-001, x-app-mode: debug

# Response (First Call)
{
  "message": "Guest user created",
  "user_role": "guest",
  "user": {"userId": "guest_be013046", "is_guest": true},
  "tokens": {...}
}

# Response (Second Call - Same Device)
{
  "message": "Guest user found",
  "user_role": "guest",
  "user": {"userId": "guest_be013046", "is_guest": true},
  "tokens": {...}
}
```
✅ **PASSED**: Guest user creation and retrieval working

### Test 2: Signup with Device-ID
```bash
# Request
POST /auth/signup/
Headers: x-device-id: device-signup-001, x-app-mode: debug

# Response
{
  "show_otp": false,
  "message": "User created successfully (debug mode)",
  "user_role": "user",
  "user": {...},
  "tokens": {...}
}
```
✅ **PASSED**: Signup accepts device-id header

### Test 3: Missing Required Header
```bash
# Request without x-device-id
POST /auth/signup/
Headers: x-app-mode: debug

# Response
{
  "error": "x-device-id header is required"
}
```
✅ **PASSED**: Mandatory header validation working

### Test 4: Debug Mode OTP
```bash
# Signup in release mode
POST /auth/signup/
Headers: x-device-id: flow001, x-app-mode: release
Response: {"show_otp": true}

# OTP verification in debug mode with fixed OTP
POST /auth/verify-otp/
Headers: x-device-id: flow001, x-app-mode: debug
Body: {"identifier": "flow@test.com", "entered_otp": "123456"}

# Response
{
  "message": "User created successfully",
  "user_role": "user",
  "user": {"userId": "flow", ...},
  "tokens": {...}
}
```
✅ **PASSED**: Debug mode accepts fixed OTP 123456

### Test 5: Release Mode OTP
```bash
# Signup in release mode
POST /auth/signup/
Headers: x-device-id: device-otp-002, x-app-mode: release
Body: {"number": "9988776655", ...}

# Response
{
  "show_otp": true,
  "message": "OTP sent successfully via SMS/Email",
  "identifier": "9988776655"
}
```
✅ **PASSED**: Release mode requests real OTP

## 📋 Database Changes

### UserProfile Model
- Added `device_id` field (CharField, indexed, nullable, unique)
- Links to guest → user upgrade flow

### PendingSignup Model
- Added `device_id` field (CharField, indexed, nullable)
- Tracks device during OTP verification

## 🔄 Complete User Flow

### Flow 1: Guest → Authenticated User
```
1. User opens app (no login)
   → POST /app-init/ with x-device-id
   → Auto-create guest user with device_id
   → Return guest tokens

2. User signs up for real account
   → POST /auth/signup/ with same x-device-id
   → Store device_id in pending signup

3. User verifies OTP
   → POST /auth/verify-otp/ with x-device-id
   → Check if guest exists with this device_id
   → If yes: upgrade guest record (DON'T create new)
   → Return user tokens
```

### Flow 2: Direct Login
```
1. User signs up
   → POST /auth/signup/ with x-device-id and email/phone

2. In debug mode: User created immediately
   → Return tokens with show_otp: false

3. In release mode: OTP verification required
   → POST /auth/verify-otp/
   → Return tokens with user data
```

## 📝 API Examples

### App Init
```bash
curl -X POST http://localhost:8000/app-init/ \
  -H "Content-Type: application/json" \
  -H "x-device-id: device-001" \
  -H "x-app-mode: debug" \
  -d '{}'
```

### Signup
```bash
curl -X POST http://localhost:8000/auth/signup/ \
  -H "Content-Type: application/json" \
  -H "x-device-id: device-001" \
  -H "x-app-mode: debug" \
  -d '{
    "email_id": "user@test.com",
    "password": "Pass@123",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": ["tech", "music"]
  }'
```

### Verify OTP
```bash
curl -X POST http://localhost:8000/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -H "x-device-id: device-001" \
  -H "x-app-mode: debug" \
  -d '{
    "identifier": "user@test.com",
    "entered_otp": "123456"
  }'
```

## 🔒 Security Considerations

1. **Device ID Tracking**: Used for guest → user upgrade, enables per-device analytics
2. **Debug Mode**: Only use in development, NODE_ENV=development AND x-app-mode=debug
3. **OTP Validation**: Different logic for debug vs production
4. **Mandatory Headers**: x-device-id required in all API calls

## 📊 Response Fields

All responses now include:
- `user_role`: 'guest' or 'user' to distinguish user types
- Proper error messages for missing headers
- Location details in signup/OTP verification responses

## ✨ Benefits

1. **Smooth Onboarding**: Users can explore as guests before signing up
2. **Device Tracking**: Understand user patterns and device lifecycle
3. **Development Friendly**: Easy testing with fixed OTP in debug mode
4. **Production Ready**: Real OTP flow in release mode
5. **No User Duplication**: Guest record updated on upgrade, not replaced
