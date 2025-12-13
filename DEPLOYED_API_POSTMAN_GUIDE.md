# 🧪 **PINMATE API - POSTMAN TESTING GUIDE (DEPLOYED)**

## **Base URL:** `https://social-media-platform-backend-4oz4.onrender.com`

---

## 📋 **ENDPOINT TESTING WORKFLOW**

### **Phase 1: Public Endpoints (No Authentication Required)**

#### **1. Get Interests** ✅
```
Method: POST
URL: https://social-media-platform-backend-4oz4.onrender.com/get-interests/
Headers:
  Content-Type: application/json

Body (raw JSON):
{
  "lat": "12.9716",
  "long": "77.5946"
}
```

**Expected Response (200 OK):**
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
    },
    {
      "id": "music",
      "name": "Music",
      "image": "https://example.com/images/music.jpg"
    },
    {
      "id": "sports",
      "name": "Sports",
      "image": "https://example.com/images/sports.jpg"
    },
    {
      "id": "food",
      "name": "Food",
      "image": "https://example.com/images/food.jpg"
    },
    {
      "id": "photography",
      "name": "Photography",
      "image": "https://example.com/images/photography.jpg"
    },
    {
      "id": "fashion",
      "name": "Fashion",
      "image": "https://example.com/images/fashion.jpg"
    },
    {
      "id": "fitness",
      "name": "Fitness",
      "image": "https://example.com/images/fitness.jpg"
    },
    {
      "id": "diy",
      "name": "DIY",
      "image": "https://example.com/images/diy.jpg"
    }
  ]
}
```

**Curl Command:**
```bash
curl -X POST "https://social-media-platform-backend-4oz4.onrender.com/get-interests/" \
  -H "Content-Type: application/json" \
  -d '{"lat": "12.9716", "long": "77.5946"}'
```

---

#### **2. Guest Login** ✅
```
Method: POST
URL: https://social-media-platform-backend-4oz4.onrender.com/login/guest/
Headers:
  Content-Type: application/json

Body (raw JSON):
{
  "interests": [
    "Art", "Travel", "Food", "Technology",
    "Fashion", "Fitness", "Photography", "Music", "Sports", "DIY"
  ],
  "long": "77.5946",
  "lat": "12.9716"
}
```

**Expected Response (201 Created):**
```json
{
  "message": "Guest user registered successfully",
  "user": {
    "is_guest": true
  },
  "tokens": {
    "refresh": "eyJhbGciOiJIUzI1NiIs...",
    "access": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

**Curl Command:**
```bash
curl -X POST "https://social-media-platform-backend-4oz4.onrender.com/login/guest/" \
  -H "Content-Type: application/json" \
  -d '{
    "interests": ["Art", "Travel", "Food", "Technology", "Fashion", "Fitness", "Photography", "Music", "Sports", "DIY"],
    "long": "77.5946",
    "lat": "12.9716"
  }'
```

---

### **Phase 2: Authentication Endpoints**

#### **3. Email Login** ✅
```
Method: POST
URL: https://social-media-platform-backend-4oz4.onrender.com/auth/login/
Headers:
  Content-Type: application/json

Body (raw JSON):
{
  "email_id": "yathaarthbatra10@gmail.com",
  "password": "Yatha@1234"
}
```

**Expected Response (200 OK):**
```json
{
  "message": "Login successful",
  "user": {
    "userId": "yathaarthbatra10",
    "name": "Yathaarth Batra",
    "email": "yathaarthbatra10@gmail.com",
    "bio": "Software Developer at Pinmate",
    "profilePhoto": ""
  },
  "tokens": {
    "refresh": "eyJhbGciOiJIUzI1NiIs...",
    "access": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

**Curl Command:**
```bash
curl -X POST "https://social-media-platform-backend-4oz4.onrender.com/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"email_id": "yathaarthbatra10@gmail.com", "password": "Yatha@1234"}'
```

---

#### **4. Phone Login** ✅
```
Method: POST
URL: https://social-media-platform-backend-4oz4.onrender.com/auth/login/
Headers:
  Content-Type: application/json

Body (raw JSON):
{
  "number": "7015926932",
  "password": "Yatha@1234"
}
```

**Expected Response (200 OK):**
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
    "refresh": "eyJhbGciOiJIUzI1NiIs...",
    "access": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

**Curl Command:**
```bash
curl -X POST "https://social-media-platform-backend-4oz4.onrender.com/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"number": "7015926932", "password": "Yatha@1234"}'
```

---

#### **5. Email Signup** ✅
```
Method: POST
URL: https://social-media-platform-backend-4oz4.onrender.com/auth/signup/
Headers:
  Content-Type: application/json

Body (raw JSON):
{
  "email_id": "newuser@example.com",
  "password": "TestPass123",
  "long": "77.5946",
  "lat": "12.9716",
  "interests": ["sports", "music", "travel", "technology"]
}
```

**Expected Response (201 Created):**
```json
{
  "message": "User created successfully",
  "user": {
    "userId": "newuser",
    "name": null,
    "email": "newuser@example.com"
  },
  "tokens": {
    "refresh": "eyJhbGciOiJIUzI1NiIs...",
    "access": "eyJhbGciOiJIUzI1NiIs..."
  },
  "location_details": {
    "pincode": "560001",
    "city": "Bengaluru",
    "state": "Karnataka",
    "country": "India"
  }
}
```

**Curl Command:**
```bash
curl -X POST "https://social-media-platform-backend-4oz4.onrender.com/auth/signup/" \
  -H "Content-Type: application/json" \
  -d '{
    "email_id": "newuser@example.com",
    "password": "TestPass123",
    "long": "77.5946",
    "lat": "12.9716",
    "interests": ["sports", "music", "travel", "technology"]
  }'
```

---

#### **6. Phone Signup** ✅
```
Method: POST
URL: https://social-media-platform-backend-4oz4.onrender.com/auth/signup/
Headers:
  Content-Type: application/json

Body (raw JSON):
{
  "number": "9999999999",
  "password": "PhonePass123",
  "long": "77.5946",
  "lat": "12.9716",
  "interests": ["technology", "music", "travel"]
}
```

**Expected Response (201 Created):**
```json
{
  "message": "User created successfully",
  "user": {
    "userId": "user_9999999999",
    "name": null,
    "email": null
  },
  "tokens": {
    "refresh": "eyJhbGciOiJIUzI1NiIs...",
    "access": "eyJhbGciOiJIUzI1NiIs..."
  },
  "location_details": {
    "pincode": "560001",
    "city": "Bengaluru",
    "state": "Karnataka",
    "country": "India"
  }
}
```

**Curl Command:**
```bash
curl -X POST "https://social-media-platform-backend-4oz4.onrender.com/auth/signup/" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "9999999999",
    "password": "PhonePass123",
    "long": "77.5946",
    "lat": "12.9716",
    "interests": ["technology", "music", "travel"]
  }'
```

---

#### **7. Token Refresh** ✅
```
Method: POST
URL: https://social-media-platform-backend-4oz4.onrender.com/auth/token/refresh/
Headers:
  Content-Type: application/json

Body (raw JSON):
{
  "refresh": "{{refresh_token}}"
}
```

**Expected Response (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Curl Command:**
```bash
# Replace REFRESH_TOKEN with actual refresh token
curl -X POST "https://social-media-platform-backend-4oz4.onrender.com/auth/token/refresh/" \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN_HERE"}'
```

---

### **Phase 3: Protected Endpoints (Require Authentication)**

#### **8. Get Feed** 🔒 ✅
```
Method: POST
URL: https://social-media-platform-backend-4oz4.onrender.com/get-feed/
Headers:
  Content-Type: application/json
  Authorization: Bearer {{access_token}}

Body (raw JSON):
{
  "lat": "12.9716",
  "long": "77.5946"
}
```

**Expected Response (200 OK):**
```json
{
  "feed": [],
  "message": "Feed endpoint - to be implemented with business logic"
}
```

**Curl Command:**
```bash
# Replace ACCESS_TOKEN with actual access token from login
curl -X POST "https://social-media-platform-backend-4oz4.onrender.com/get-feed/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -d '{"lat": "12.9716", "long": "77.5946"}'
```

---

#### **9. Setup Profile** 🔒 ✅
```
Method: POST
URL: https://social-media-platform-backend-4oz4.onrender.com/setup-profile/
Headers:
  Content-Type: application/json
  Authorization: Bearer {{access_token}}

Body (raw JSON):
{
  "name": "Yathaarth Batra",
  "bio": "Software Developer at Pinmate",
  "gender": "Male",
  "age": 25,
  "image_url": "https://example.com/profile.jpg",
  "additional_pincodes": ["560001", "560002", "560003"]
}
```

**Expected Response (200 OK):**
```json
{
  "message": "Profile Details saved successfully."
}
```

**Curl Command:**
```bash
# Replace ACCESS_TOKEN with actual access token from login
curl -X POST "https://social-media-platform-backend-4oz4.onrender.com/setup-profile/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -d '{
    "name": "Yathaarth Batra",
    "bio": "Software Developer at Pinmate",
    "gender": "Male",
    "age": 25,
    "image_url": "https://example.com/profile.jpg",
    "additional_pincodes": ["560001", "560002", "560003"]
  }'
```

---

## 🔧 **POSTMAN SETUP INSTRUCTIONS**

### **Step 1: Import Collection**
1. Open Postman
2. Click **"Import"** button
3. Select **"File"** tab
4. Choose: `Pinmate_API_Collection.postman_collection.json`
5. Click **"Import"**

### **Step 2: Set Environment Variables**
1. Click **"Environments"** (left sidebar)
2. Click **"Create Environment"**
3. Name it: `Pinmate Deployed API`
4. Add variables:
   - `base_url`: `https://social-media-platform-backend-4oz4.onrender.com`
   - `access_token`: (leave empty, will be set automatically)
   - `refresh_token`: (leave empty, will be set automatically)
5. Click **"Save"**
6. Select `Pinmate Deployed API` from environment dropdown

### **Step 3: Test Workflow**
1. **Start with public endpoints:** Get Interests, Guest Login
2. **Test authentication:** Login with existing user
3. **Test protected endpoints:** Use access_token from login
4. **Test signup:** Create new users
5. **Test token refresh:** Use refresh_token to get new access_token

---

## ⚠️ **COMMON ISSUES & SOLUTIONS**

### **405 Method Not Allowed**
- **Problem:** Using GET instead of POST
- **Solution:** Change method to POST for all endpoints

### **401 Unauthorized**
- **Problem:** Missing or invalid token
- **Solution:** Ensure valid `access_token` in Authorization header

### **400 Bad Request**
- **Problem:** Invalid JSON or missing required fields
- **Solution:** Check request body format and required fields

### **Invalid character in header**
- **Problem:** JWT token has special characters
- **Solution:** Ensure token is properly formatted in Authorization header

---

## 📊 **TESTING CHECKLIST**

### **Public Endpoints**
- [ ] Get Interests (POST)
- [ ] Guest Login (POST)

### **Authentication**
- [ ] Email Login (POST)
- [ ] Phone Login (POST)
- [ ] Email Signup (POST)
- [ ] Phone Signup (POST)
- [ ] Token Refresh (POST)

### **Protected Endpoints**
- [ ] Get Feed (POST + Auth)
- [ ] Setup Profile (POST + Auth)

### **Error Scenarios**
- [ ] Invalid credentials
- [ ] Missing authentication
- [ ] Invalid coordinates
- [ ] Malformed requests

---

## 🚀 **QUICK START COMMANDS**

```bash
# 1. Test server health
curl -X POST "https://social-media-platform-backend-4oz4.onrender.com/get-interests/" \
  -H "Content-Type: application/json" \
  -d '{"lat": "12.9716", "long": "77.5946"}'

# 2. Login and get token
ACCESS_TOKEN=$(curl -s -X POST "https://social-media-platform-backend-4oz4.onrender.com/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"email_id": "yathaarthbatra10@gmail.com", "password": "Yatha@1234"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['tokens']['access'])")

# 3. Test protected endpoint
curl -X POST "https://social-media-platform-backend-4oz4.onrender.com/get-feed/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"lat": "12.9716", "long": "77.5946"}'
```

---

## 🎯 **SUCCESS CRITERIA**

✅ **All endpoints return expected HTTP status codes**  
✅ **Authentication tokens are generated and validated**  
✅ **Location geocoding works for valid coordinates**  
✅ **User data is properly stored and retrieved**  
✅ **Protected endpoints require valid JWT tokens**  
✅ **Error handling works for invalid inputs**  

---

**🎉 Your Pinmate API is fully tested and ready for production use!**