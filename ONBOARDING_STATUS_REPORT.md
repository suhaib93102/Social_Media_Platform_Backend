# Pinmate Onboarding API - Status Report

## ✅ Implementation Status

### Already Implemented Features:

1. **Save Interests API** ✅
   - Endpoint: `POST /save-interests/`
   - Supports authenticated users
   - Accepts `interests` array in request body
   - Returns: `{"message": "Interests added", "interests": [...]}`

2. **OTP Verification Flow** ✅
   - Endpoint: `POST /auth/verify-otp/`
   - Verifies OTP and completes user registration
   - Returns same response as signup with tokens

3. **Debug Mode Support** ✅
   - Checks `Is-Debug` or `is_debug` header in requests
   - When `true`: Skips OTP verification, creates user immediately
   - When `false`: Sends OTP and requires verification
   - Returns `show_otp: true/false` in signup response

4. **Address Details in Profile** ✅
   - Field: `address_details` (text field)
   - Already supported in `setup-profile` endpoint
   - Accepts `address_details` string in request

5. **Input Validation** ✅
   - Phone number: 10 digits, numeric only
   - Coordinates: lat (-90 to 90), long (-180 to 180)
   - Pincode: 6 digits (Indian format)

## 📋 Complete API Specification

### 1. **Sign Up (Email)**
```
POST /auth/signup/
Headers: Is-Debug: true/false
Request:
{
  "email_id": "yathaarthbatra10@gmail.com",
  "password": "Yatha@1234",
  "lat": "28.6139",
  "long": "77.2090",
  "interests": ["sports", "music", "travel", "technology"]
}

Response (Debug Mode):
{
  "show_otp": false,
  "message": "User created successfully (debug mode)",
  "user": {
    "userId": "yathaarthbatra10",
    "name": null,
    "email": "yathaarthbatra10@gmail.com"
  },
  "tokens": {
    "refresh": "eyJ...",
    "access": "eyJ..."
  },
  "location_details": {
    "pincode": "110001",
    "city": "New Delhi",
    "state": "Delhi",
    "country": "India"
  }
}

Response (Production Mode):
{
  "show_otp": true,
  "message": "OTP sent successfully",
  "identifier": "yathaarthbatra10@gmail.com"
}
```

### 2. **Sign Up (Phone)**
```
POST /auth/signup/
Headers: Is-Debug: true/false
Request:
{
  "number": "9876543210",
  "password": "Yatha@1234",
  "lat": "28.6139",
  "long": "77.2090",
  "interests": ["technology", "music", "travel"]
}

Response: Same as email signup
```

### 3. **Verify OTP**
```
POST /auth/verify-otp/
Request:
{
  "identifier": "yathaarthbatra10@gmail.com",
  "entered_otp": "123456"
}

Response:
{
  "message": "User created successfully",
  "user": {
    "userId": "yathaarthbatra10",
    "name": null,
    "email": "yathaarthbatra10@gmail.com"
  },
  "tokens": {
    "refresh": "eyJ...",
    "access": "eyJ..."
  },
  "location_details": {
    "pincode": "110001",
    "city": "New Delhi",
    "state": "Delhi",
    "country": "India"
  }
}
```

### 4. **Login (Email)**
```
POST /auth/login/
Request:
{
  "email_id": "yathaarthbatra10@gmail.com",
  "password": "Yatha@1234"
}

Response:
{
  "message": "Login successful",
  "user": {
    "userId": "yathaarthbatra10",
    "name": "Yathaarth Batra",
    "email": "yathaarthbatra10@gmail.com",
    "bio": null,
    "profilePhoto": null
  },
  "tokens": {
    "refresh": "eyJ...",
    "access": "eyJ..."
  }
}
```

### 5. **Login (Phone)**
```
POST /auth/login/
Request:
{
  "number": "9876543210",
  "password": "Yatha@1234"
}

Response: Same as email login
```

### 6. **Get Interests**
```
POST /get-interests/
Request:
{
  "lat": "28.6139",
  "long": "77.2090"
}

Response:
{
  "interests": [
    {
      "name": "Technology",
      "id": "tech",
      "image": "https://example.com/images/technology.jpg"
    },
    {
      "name": "Art",
      "id": "art",
      "image": "https://example.com/images/art.jpg"
    }
  ]
}
```

### 7. **Save Interests**
```
POST /save-interests/
Headers: Authorization: Bearer <access_token>
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

### 8. **Guest Login**
```
POST /login/guest/
Headers: Is-Debug: true/false
Request:
{
  "interests": ["Art", "Travel", "Food", "Technology"],
  "lat": "28.6139",
  "long": "77.2090"
}

Response:
{
  "message": "Guest user registered successfully",
  "user": {
    "is_guest": true
  },
  "tokens": {
    "refresh": "eyJ...",
    "access": "eyJ..."
  }
}
```

### 9. **Setup Profile**
```
POST /setup-profile/
Headers: Authorization: Bearer <access_token>
Request:
{
  "name": "Yathaarth Batra",
  "bio": "Software Developer at Pinmate",
  "gender": "Male",
  "age": 25,
  "image_url": "https://example.com/profile.jpg",
  "additional_pincodes": ["560002", "560003", "560004"],
  "address_details": "123 Main Street, Apartment 4B, Near City Center"
}

Response:
{
  "message": "Profile Details saved successfully."
}
```

### 10. **Get Feed**
```
POST /get-feed/
Headers: Authorization: Bearer <access_token>
Request:
{
  "lat": "37.7749",
  "long": "-122.4194"
}

Response:
{
  "feed": [...]
}
```

## 💰 Nominatim Pricing & Usage Policy

### OpenStreetMap Nominatim - FREE Service
- **Cost**: 100% FREE for all usage
- **Usage Policy**: Fair use - max 1 request/second
- **For 10k users**: Completely FREE

### Important Considerations:

1. **Rate Limiting**:
   - Maximum 1 request per second
   - For 10k simultaneous users, you'll need caching or alternatives

2. **Caching Strategy** (Recommended):
   - Cache reverse geocoding results in database
   - Store pincode/city/state for each coordinate pair
   - Reduces API calls by 95%+
   - Example: Cache validity = 30 days

3. **Alternatives for High Volume**:

   a) **Google Maps Geocoding API**
      - Cost: $5 per 1000 requests
      - For 10k users: ~$50/month (if each user makes 1 request)
      - Pros: High rate limits, accurate
      - Cons: Paid service

   b) **Mapbox Geocoding API**
      - Cost: FREE up to 100k requests/month
      - Beyond that: $0.50 per 1000 requests
      - For 10k users: FREE (if under 100k/month)
      - Pros: Generous free tier
      - Cons: Requires account

   c) **LocationIQ**
      - Cost: FREE up to 10k requests/day
      - Beyond that: $49/month for 100k/day
      - For 10k users: FREE with rate limits
      - Pros: Similar to Nominatim but hosted
      - Cons: Lower free tier than Mapbox

4. **Recommended Setup for Production**:
   ```python
   # Implement caching layer
   - Check if coordinates exist in cache (Redis/DB)
   - If cached and < 30 days old, return cached result
   - Otherwise, call Nominatim API
   - Cache the result
   
   # This reduces API calls by 90%+
   ```

5. **Current Implementation**:
   - Using Nominatim (FREE)
   - No caching yet (should be added)
   - Good for MVP/testing
   - For production with 10k users, add caching

## 🔧 Technical Implementation Details

### Models:
- `UserProfile`: Main user model with address_details field
- `OTPVerification`: Stores OTP codes with expiration
- `PendingSignup`: Stores signup data until OTP verified
- `Interest`: Predefined interests for selection

### Authentication:
- JWT tokens (access + refresh)
- Token-based auth for protected endpoints
- Guest users also receive tokens

### Validation:
- Phone: 10 digits, numeric only, auto-cleaning
- Coordinates: lat (-90 to 90), long (-180 to 180)
- Pincode: 6 digits (Indian format)

### Debug Mode:
- Header: `Is-Debug: true`
- Skips OTP verification
- Returns `show_otp: false` in response
- Immediately creates user and returns tokens

## ✅ All Requirements Status

| Requirement | Status | Notes |
|------------|--------|-------|
| Email Signup | ✅ Complete | With OTP support |
| Phone Signup | ✅ Complete | With OTP support |
| Email Login | ✅ Complete | - |
| Phone Login | ✅ Complete | - |
| OTP Verification | ✅ Complete | verify-otp endpoint |
| Debug Mode | ✅ Complete | Is-Debug header |
| Save Interests | ✅ Complete | Authenticated endpoint |
| Get Interests | ✅ Complete | Location-based |
| Guest Login | ✅ Complete | With interests |
| Setup Profile | ✅ Complete | Including address_details |
| Get Feed | ✅ Complete | Location-based |
| Input Validation | ✅ Complete | Phone, coords, pincode |
| Address in Profile | ✅ Complete | address_details field |

## 🎯 Next Steps

1. **Test all endpoints locally** ✓
2. **Add caching for geocoding** (recommended for production)
3. **Setup email/SMS service** (currently console-only)
4. **Monitor API usage** (Nominatim rate limits)
5. **Consider alternative geocoding service** (for scale)

## 📝 Notes

- All endpoints tested and working
- OTP is printed to console (not sent via email/SMS yet)
- Debug mode allows testing without real OTP
- Nominatim is FREE but has rate limits (1 req/sec)
- For 10k users, implement caching to avoid rate limits
