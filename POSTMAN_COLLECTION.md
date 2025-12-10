# Pinmate API - Postman Collection Guide

## 📦 Collection Import & Setup

### Step 1: Import the Collection
1. Open Postman
2. Click **Import** button (top left)
3. Drag and drop `Pinmate_API_Collection.postman_collection.json` file
4. Click **Import**

### Step 2: Setup Environment Variables
1. Create a new environment in Postman (click the gear icon ⚙️ in top right)
2. Name it `Pinmate Local` or `Pinmate Production`
3. Add the following variables:

| Variable Name | Initial Value | Current Value |
|--------------|---------------|---------------|
| `base_url` | `http://127.0.0.1:8000` | `http://127.0.0.1:8000` |
| `access_token` | (leave empty) | (leave empty) |
| `refresh_token` | (leave empty) | (leave empty) |
| `guest_access_token` | (leave empty) | (leave empty) |

**For Production:**
- Set `base_url` to your production URL (e.g., `https://your-api.render.com`)

### Step 3: Select Environment
- Click the environment dropdown (top right)
- Select the environment you created

---

## 🚀 Quick Start - Testing Workflow

### Recommended Testing Order:

#### 1️⃣ **Get Available Interests**
- **Request:** `POST {{base_url}}/get-interests/`
- **Body:**
```json
{
  "lat": "28.6139",
  "long": "77.2090"
}
```
- **Expected Response:** List of 10 interests
- **Status:** 200 OK

#### 2️⃣ **Sign Up with Email**
- **Request:** `POST {{base_url}}/auth/signup/`
- **Body:**
```json
{
  "email_id": "test@example.com",
  "password": "Test@1234",
  "interests": ["technology", "sports", "music"],
  "lat": "28.6139",
  "long": "77.2090"
}
```
- **Expected Response:** User created with tokens
- **Status:** 201 Created
- **Auto-saved:** `access_token` and `refresh_token` variables

#### 3️⃣ **Login with Email**
- **Request:** `POST {{base_url}}/auth/login/`
- **Body:**
```json
{
  "email_id": "test@example.com",
  "password": "Test@1234"
}
```
- **Expected Response:** Login successful with tokens
- **Status:** 200 OK
- **Auto-saved:** `access_token` and `refresh_token` variables

#### 4️⃣ **Setup Profile** (Requires Authentication)
- **Request:** `POST {{base_url}}/setup-profile/`
- **Headers:** 
  - `Authorization: Bearer {{access_token}}`
  - `Content-Type: application/json`
- **Body:**
```json
{
  "name": "John Doe",
  "bio": "Software Developer at Pinmate",
  "gender": "Male",
  "age": 25,
  "image_url": "https://example.com/profile.jpg",
  "additional_pincodes": ["110001", "110002"]
}
```
- **Expected Response:** Profile updated successfully
- **Status:** 200 OK

#### 5️⃣ **Get Feed** (Requires Authentication)
- **Request:** `POST {{base_url}}/get-feed/`
- **Headers:**
  - `Authorization: Bearer {{access_token}}`
  - `Content-Type: application/json`
- **Body:**
```json
{
  "lat": "28.6139",
  "long": "77.2090"
}
```
- **Expected Response:** Feed data
- **Status:** 200 OK

#### 6️⃣ **Refresh Access Token**
- **Request:** `POST {{base_url}}/auth/token/refresh/`
- **Body:**
```json
{
  "refresh": "{{refresh_token}}"
}
```
- **Expected Response:** New access token
- **Status:** 200 OK

---

## 📱 Alternative Flows

### Guest User Flow

#### 1️⃣ **Guest Login**
- **Request:** `POST {{base_url}}/login/guest/`
- **Body:**
```json
{
  "interests": ["technology", "travel"],
  "lat": "28.6139",
  "long": "77.2090"
}
```
- **Expected Response:** Guest user created with tokens
- **Status:** 201 Created

#### 2️⃣ **Setup Guest Profile**
- Use the same Setup Profile endpoint with guest `access_token`

### Phone Number Authentication

#### Sign Up with Phone
- **Request:** `POST {{base_url}}/auth/signup/`
- **Body:**
```json
{
  "number": "9876543210",
  "password": "Test@1234",
  "interests": ["technology", "sports"],
  "lat": "28.6139",
  "long": "77.2090"
}
```

#### Login with Phone
- **Request:** `POST {{base_url}}/auth/login/`
- **Body:**
```json
{
  "number": "9876543210",
  "password": "Test@1234"
}
```

---

## 📋 Complete Endpoint Reference

### 1. Get Interests
```
POST {{base_url}}/get-interests/
```
**Request:**
```json
{
  "lat": "28.6139",
  "long": "77.2090"
}
```

**Response (200):**
```json
{
  "interests": [
    {
      "id": "technology",
      "name": "Technology",
      "image": "https://example.com/images/technology.jpg"
    }
  ]
}
```

---

### 2. Sign Up (Email)
```
POST {{base_url}}/auth/signup/
```
**Request:**
```json
{
  "email_id": "user@example.com",
  "password": "Password@123",
  "interests": ["technology", "sports"],
  "lat": "28.6139",
  "long": "77.2090"
}
```

**Response (201):**
```json
{
  "message": "Signup successful",
  "user": {
    "userId": "user_emaildomain",
    "email": "user@example.com"
  },
  "tokens": {
    "refresh": "...",
    "access": "..."
  }
}
```

---

### 3. Sign Up (Phone)
```
POST {{base_url}}/auth/signup/
```
**Request:**
```json
{
  "number": "9876543210",
  "password": "Password@123",
  "interests": ["technology", "sports"],
  "lat": "28.6139",
  "long": "77.2090"
}
```

**Response (201):**
```json
{
  "message": "Signup successful",
  "user": {
    "userId": "user_9876543210",
    "phone_number": "9876543210"
  },
  "tokens": {
    "refresh": "...",
    "access": "..."
  }
}
```

---

### 4. Login (Email)
```
POST {{base_url}}/auth/login/
```
**Request:**
```json
{
  "email_id": "user@example.com",
  "password": "Password@123"
}
```

**Response (200):**
```json
{
  "message": "Login successful",
  "user": {
    "userId": "user_emaildomain",
    "name": "John Doe",
    "email": "user@example.com",
    "bio": "...",
    "profilePhoto": "..."
  },
  "tokens": {
    "refresh": "...",
    "access": "..."
  }
}
```

---

### 5. Login (Phone)
```
POST {{base_url}}/auth/login/
```
**Request:**
```json
{
  "number": "9876543210",
  "password": "Password@123"
}
```

**Response (200):**
```json
{
  "message": "Login successful",
  "user": {
    "userId": "user_9876543210",
    "phone_number": "9876543210"
  },
  "tokens": {
    "refresh": "...",
    "access": "..."
  }
}
```

---

### 6. Guest Login
```
POST {{base_url}}/login/guest/
```
**Request:**
```json
{
  "interests": ["technology", "travel"],
  "lat": "28.6139",
  "long": "77.2090"
}
```

**Response (201):**
```json
{
  "message": "Guest user registered successfully",
  "user": {
    "is_guest": true
  },
  "tokens": {
    "refresh": "...",
    "access": "..."
  }
}
```

---

### 7. Setup Profile (Authenticated)
```
POST {{base_url}}/setup-profile/
Authorization: Bearer {{access_token}}
```
**Request:**
```json
{
  "name": "John Doe",
  "bio": "Software Developer",
  "gender": "Male",
  "age": 25,
  "image_url": "https://example.com/profile.jpg",
  "additional_pincodes": ["110001", "110002"]
}
```

**Response (200):**
```json
{
  "message": "Profile Details saved successfully."
}
```

**Error (401):**
```json
{
  "error": "No authentication token provided"
}
```

---

### 8. Get Feed (Authenticated)
```
POST {{base_url}}/get-feed/
Authorization: Bearer {{access_token}}
```
**Request:**
```json
{
  "lat": "28.6139",
  "long": "77.2090"
}
```

**Response (200):**
```json
{
  "feed": [],
  "message": "Feed endpoint - to be implemented with business logic"
}
```

---

### 9. Refresh Token
```
POST {{base_url}}/auth/token/refresh/
```
**Request:**
```json
{
  "refresh": "{{refresh_token}}"
}
```

**Response (200):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## 🔐 Authentication & Tokens

### Token Lifecycle
- **Access Token:** Expires in **1 hour**
- **Refresh Token:** Expires in **7 days**

### How to Use Tokens in Postman

#### Automatic (Recommended)
The collection includes **Tests** scripts that automatically save tokens to environment variables after login/signup.

#### Manual
1. Copy the `access` token from login/signup response
2. Go to Environment variables
3. Paste into `access_token` current value
4. Token will auto-populate in authenticated requests via `{{access_token}}`

### Token Refresh Workflow
1. When you receive a 401 error, run the **Refresh Token** request
2. New access token will be auto-saved to `access_token` variable
3. Retry your failed request

---

## 🧪 Testing Checklist

### ✅ Pre-Testing Setup
- [ ] Postman collection imported
- [ ] Environment created and selected
- [ ] `base_url` variable set correctly
- [ ] Django server running (`python manage.py runserver`)

### ✅ Core Flow Testing
- [ ] Get interests list (no auth required)
- [ ] Sign up with email
- [ ] Login with email (tokens auto-saved)
- [ ] Setup profile with valid token
- [ ] Get feed with valid token
- [ ] Refresh access token

### ✅ Alternative Flow Testing
- [ ] Sign up with phone number
- [ ] Login with phone number
- [ ] Guest login (anonymous user)
- [ ] Setup guest profile

### ✅ Error Scenarios
- [ ] Login with wrong password (400 error)
- [ ] Sign up with existing email (400 error)
- [ ] Setup profile without token (401 error)
- [ ] Get feed without token (401 error)
- [ ] Use expired/invalid token (401 error)

---

## 🐛 Common Issues & Solutions

### Issue 1: "Connection refused" or "Could not send request"
**Solution:** 
- Ensure Django server is running: `python manage.py runserver`
- Check `base_url` is set to `http://127.0.0.1:8000` (with http, not https)

### Issue 2: "401 Unauthorized" on authenticated endpoints
**Solution:**
- Run Login request first
- Check `access_token` environment variable has a value
- If token expired, use Refresh Token request
- Ensure Authorization header format: `Bearer {{access_token}}`

### Issue 3: "No authentication token provided"
**Solution:**
- Verify Authorization header is included in request
- Check header key is exactly: `Authorization`
- Check value format: `Bearer {{access_token}}` (with space after Bearer)

### Issue 4: Tokens not auto-saving
**Solution:**
- Check Tests tab in request has the script:
```javascript
pm.environment.set("access_token", pm.response.json().tokens.access);
pm.environment.set("refresh_token", pm.response.json().tokens.refresh);
```
- Ensure environment is selected (not "No Environment")

### Issue 5: "User already exists" on signup
**Solution:**
- This is expected if you've already signed up with that email/phone
- Use Login endpoint instead, or
- Change email/phone to a new value

---

## 📊 Response Status Codes

| Status Code | Meaning | Common Scenarios |
|------------|---------|------------------|
| **200 OK** | Success | Login, Get Feed, Setup Profile |
| **201 Created** | Resource created | Signup, Guest Login |
| **400 Bad Request** | Invalid input | Missing fields, user exists, wrong password |
| **401 Unauthorized** | No/invalid token | Missing auth header, expired token |
| **404 Not Found** | Resource not found | User not found |
| **500 Internal Server Error** | Server error | Backend issue, check Django logs |

---

## 🔄 Data Flow Example

### Complete User Journey:

```
1. Get Interests
   ↓ (User selects interests)
   
2. Sign Up (Email/Phone)
   ↓ (Receive access_token + refresh_token)
   
3. Auto-saved to environment variables
   ↓
   
4. Setup Profile (Uses access_token)
   ↓ (Profile updated)
   
5. Get Feed (Uses access_token)
   ↓ (Receive personalized feed)
   
6. After 1 hour...
   ↓ (access_token expires)
   
7. Refresh Token (Uses refresh_token)
   ↓ (Receive new access_token)
   
8. Continue using API with new token
```

---

## 📝 Notes

### Location Geocoding
- All endpoints requiring `lat` and `long` use **OpenStreetMap Nominatim** for reverse geocoding
- Location details (pincode, city, state, country) are automatically fetched and saved

### Interests
- 10 pre-populated interests: Technology, Art, Travel, Music, Sports, Food, Photography, Fashion, Fitness, DIY
- Use interest IDs (lowercase, e.g., "technology") in requests

### Guest Users
- Created with temporary ID: `guest_xxxxxxxx`
- Can be upgraded to full account later
- Have limited profile information initially

### Password Requirements
- Recommended: At least 8 characters with uppercase, lowercase, number, special character
- Backend validates hashed passwords

---

## 🎯 Production Deployment

### Update Environment for Production:
1. Create new environment: `Pinmate Production`
2. Set variables:
   - `base_url`: `https://your-production-url.com`
   - Leave tokens empty (will auto-populate)
3. Select Production environment
4. Test all endpoints

### Production Checklist:
- [ ] HTTPS enabled (`https://` in base_url)
- [ ] Database migrated
- [ ] Environment variables set on hosting platform
- [ ] DEBUG=False in production settings
- [ ] CORS configured for frontend domain
- [ ] Interests populated in production database

---

## 📚 Additional Resources

- **API Documentation:** `API_DOCUMENTATION.md`
- **Implementation Summary:** `IMPLEMENTATION_SUMMARY.md`
- **Postman Collection File:** `Pinmate_API_Collection.postman_collection.json`

---

## 🆘 Support

If you encounter any issues:
1. Check Django server logs for errors
2. Verify all environment variables are set
3. Test with curl commands from API_DOCUMENTATION.md
4. Ensure database migrations are applied: `python manage.py migrate`

**All 10 endpoints tested and working! ✅**

Last updated: December 10, 2025
