# Pinmate API Documentation

## Overview
This document describes all the Pinmate API endpoints for user onboarding, authentication, and profile management.

**Base URL (Local):** `http://127.0.0.1:8000`  
**Base URL (Production):** `https://social-media-platform-backend-4oz4.onrender.com`

---

## Authentication Endpoints

### 1. Email Signup
**Endpoint:** `POST /auth/signup/`

**Request:**
```json
{
  "email_id": "yathaarthbatra10@gmail.com",
  "password": "Yatha@1234",
  "lat": "28.7041",
  "long": "77.1025",
  "interests": ["sports", "music", "travel", "technology"]
}
```

**Response (201 Created):**
```json
{
  "message": "User created successfully",
  "user": {
      "userId": "yathaarthbatra10",
      "name": null,
      "email": "yathaarthbatra10@gmail.com"
  },
  "tokens": {
      "refresh": "eyJhbGciOi...",
      "access": "eyJhbGciOi..."
  },
  "location_details": {
       "pincode": "110083",
       "city": "Delhi",
       "state": "Delhi",
       "country": "India"
  }
}
```

---

### 2. Phone Number Signup
**Endpoint:** `POST /auth/signup/`

**Request:**
```json
{
  "number": "7015926932",
  "password": "Yatha@1234",
  "lat": "12.9716",
  "long": "77.5946",
  "interests": ["technology", "music", "travel"]
}
```

**Response (201 Created):**
```json
{
  "message": "User created successfully",
  "user": {
      "userId": "user_7015926932",
      "name": null,
      "email": null
  },
  "tokens": {
      "refresh": "eyJhbGciOi...",
      "access": "eyJhbGciOi..."
  },
  "location_details": {
       "pincode": "560001",
       "city": "Bengaluru",
       "state": "Karnataka",
       "country": "India"
  }
}
```

---

### 3. Email Login
**Endpoint:** `POST /auth/login/`

**Request:**
```json
{
   "email_id": "yathaarthbatra10@gmail.com",
   "password": "Yatha@1234"
}
```

**Response (200 OK):**
```json
{
   "message": "Login successful",
   "user": {
       "userId": "yathaarthbatra10",
       "name": "Yathaarth Batra",
       "email": "yathaarthbatra10@gmail.com",
       "bio": "Software Developer",
       "profilePhoto": "https://example.com/profile.jpg"
   },
   "tokens": {
       "refresh": "eyJhbGciOi...",
       "access": "eyJhbGciOi..."
   }
}
```

---

### 4. Phone Number Login
**Endpoint:** `POST /auth/login/`

**Request:**
```json
{
   "number": "7015926932",
   "password": "Yatha@1234"
}
```

**Response (200 OK):**
```json
{
   "message": "Login successful",
   "user": {
       "userId": "user_7015926932",
       "name": null,
       "email": null,
       "bio": null,
       "profilePhoto": null
   },
   "tokens": {
       "refresh": "eyJhbGciOi...",
       "access": "eyJhbGciOi..."
   }
}
```

---

### 5. Token Refresh
**Endpoint:** `POST /auth/token/refresh/`

**Request:**
```json
{
   "refresh": "eyJhbGciOi..."
}
```

**Response (200 OK):**
```json
{
   "access": "eyJhbGciOi..."
}
```

---

## Onboarding Endpoints

### 6. Get Interests
**Endpoint:** `POST /get-interests/`

**Request:**
```json
{
   "lat": "28.7041",
   "long": "77.1025"
}
```

**Response (200 OK):**
```json
{
   "interests": [
       {
           "id": "technology",
           "name": "Technology",
           "image": "https://example.com/images/technology.jpg"
       },
       {
           "id": "art",
           "name": "Art",
           "image": "https://example.com/images/art.jpg"
       },
       {
           "id": "travel",
           "name": "Travel",
           "image": "https://example.com/images/travel.jpg"
       }
       // ... more interests
   ]
}
```

---

### 7. Guest Login
**Endpoint:** `POST /login/guest/`

**Request:**
```json
{
   "interests": ["Art", "Travel", "Food", "Technology"],
   "lat": "28.613939",
   "long": "77.209021"
}
```

**Response (201 Created):**
```json
{
  "message": "Guest user registered successfully",
  "user": {
      "is_guest": true
  },
  "tokens": {
      "refresh": "eyJhbGciOi...",
      "access": "eyJhbGciOi..."
  }
}
```

---

## Profile Endpoints (Require Authentication)

### 8. Setup Profile
**Endpoint:** `POST /setup-profile/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request:**
```json
{
   "name": "Yathaarth Batra",
   "bio": "Software Developer at Pinmate",
   "gender": "Male",
   "age": 25,
   "image_url": "https://example.com/profile.jpg",
   "additional_pincodes": ["560002", "560003", "560004"]
}
```

**Response (200 OK):**
```json
{
   "message": "Profile Details saved successfully."
}
```

---

### 9. Get Feed
**Endpoint:** `POST /get-feed/`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request:**
```json
{
   "lat": "37.7749",
   "long": "-122.4194"
}
```

**Response (200 OK):**
```json
{
   "feed": [],
   "message": "Feed endpoint - to be implemented with business logic"
}
```

---

## cURL Examples

### Email Signup
```bash
curl -X POST http://127.0.0.1:8000/auth/signup/ \
  -H "Content-Type: application/json" \
  -d '{"email_id":"user@example.com","password":"Pass@123","lat":"28.7041","long":"77.1025","interests":["sports","music"]}'
```

### Email Login
```bash
curl -X POST http://127.0.0.1:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email_id":"user@example.com","password":"Pass@123"}'
```

### Phone Signup
```bash
curl -X POST http://127.0.0.1:8000/auth/signup/ \
  -H "Content-Type: application/json" \
  -d '{"number":"9876543210","password":"Pass@123","lat":"12.9716","long":"77.5946","interests":["technology"]}'
```

### Phone Login
```bash
curl -X POST http://127.0.0.1:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"number":"9876543210","password":"Pass@123"}'
```

### Get Interests
```bash
curl -X POST http://127.0.0.1:8000/get-interests/ \
  -H "Content-Type: application/json" \
  -d '{"lat":"28.7041","long":"77.1025"}'
```

### Guest Login
```bash
curl -X POST http://127.0.0.1:8000/login/guest/ \
  -H "Content-Type: application/json" \
  -d '{"interests":["Art","Travel"],"lat":"28.613939","long":"77.209021"}'
```

### Setup Profile (with authentication)
```bash
ACCESS_TOKEN="your_access_token_here"
curl -X POST http://127.0.0.1:8000/setup-profile/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"name":"John Doe","bio":"Developer","gender":"Male","age":25,"image_url":"https://example.com/profile.jpg","additional_pincodes":["560001"]}'
```

### Get Feed (with authentication)
```bash
ACCESS_TOKEN="your_access_token_here"
curl -X POST http://127.0.0.1:8000/get-feed/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"lat":"37.7749","long":"-122.4194"}'
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Password is required"
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid credentials"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

---

## Testing

### Run Local Server
```bash
python manage.py runserver
```

### Run All Tests
```bash
python test_all_endpoints.py
```

### Populate Interests Data
```bash
python manage.py shell < populate_interests.py
```

---

## Database Models

### UserProfile Fields
- `userId` - Primary key (auto-generated from email or phone)
- `name` - User's full name (nullable)
- `email` - Email address (unique, nullable)
- `phone_number` - Phone number (unique, nullable)
- `password` - Hashed password
- `latitude`, `longitude` - User location coordinates
- `pincode`, `city`, `state`, `country` - Location details
- `interests` - Array of interest IDs
- `additional_pincodes` - Array of additional pincode strings
- `bio` - User biography
- `gender` - User gender
- `age` - User age
- `profilePhoto` - Profile photo URL
- `is_guest` - Boolean flag for guest users
- `activePincodes`, `followers`, `following` - Social features

### Interest Fields
- `interest_id` - Slug ID (primary key)
- `name` - Display name
- `image` - Image URL

---

## Notes

1. **Location Services**: The API uses OpenStreetMap's Nominatim service for reverse geocoding (lat/long → pincode/city/state/country)

2. **Token Lifetimes**:
   - Access Token: 1 hour
   - Refresh Token: 7 days

3. **User ID Generation**:
   - Email signup: Uses part before @ symbol (e.g., "yathaarthbatra10@gmail.com" → "yathaarthbatra10")
   - Phone signup: Uses "user_" prefix (e.g., "7015926932" → "user_7015926932")
   - Guest signup: Uses "guest_" + random hex (e.g., "guest_6bd9a6ce")

4. **Authentication**: Protected endpoints require `Authorization: Bearer <access_token>` header

5. **Password Hashing**: Passwords are hashed using Django's `make_password` before storage
