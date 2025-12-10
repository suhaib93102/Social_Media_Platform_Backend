# 🚀 Pinmate API - Quick Reference Card

## 📍 Base URL
```
Local:      http://127.0.0.1:8000
Production: https://your-production-url.com
```

---

## 🔑 Authentication

### Get Tokens (Login/Signup)
```bash
# Returns: { tokens: { access: "...", refresh: "..." } }
```

### Use Access Token
```bash
Authorization: Bearer <access_token>
```

### Token Expiration
- **Access:** 1 hour
- **Refresh:** 7 days

---

## 📋 All Endpoints (10 Total)

### 1️⃣ Get Interests (No Auth)
```
POST /get-interests/
Body: { "lat": "28.6139", "long": "77.2090" }
→ 200 OK
```

### 2️⃣ Sign Up - Email (No Auth)
```
POST /auth/signup/
Body: {
  "email_id": "user@example.com",
  "password": "Pass@123",
  "interests": ["technology"],
  "lat": "28.6139",
  "long": "77.2090"
}
→ 201 Created
```

### 3️⃣ Sign Up - Phone (No Auth)
```
POST /auth/signup/
Body: {
  "number": "9876543210",
  "password": "Pass@123",
  "interests": ["technology"],
  "lat": "28.6139",
  "long": "77.2090"
}
→ 201 Created
```

### 4️⃣ Login - Email (No Auth)
```
POST /auth/login/
Body: {
  "email_id": "user@example.com",
  "password": "Pass@123"
}
→ 200 OK
```

### 5️⃣ Login - Phone (No Auth)
```
POST /auth/login/
Body: {
  "number": "9876543210",
  "password": "Pass@123"
}
→ 200 OK
```

### 6️⃣ Guest Login (No Auth)
```
POST /login/guest/
Body: {
  "interests": ["technology"],
  "lat": "28.6139",
  "long": "77.2090"
}
→ 201 Created
```

### 7️⃣ Setup Profile (Requires Auth)
```
POST /setup-profile/
Headers: Authorization: Bearer <access_token>
Body: {
  "name": "John Doe",
  "bio": "Developer",
  "gender": "Male",
  "age": 25,
  "image_url": "https://...",
  "additional_pincodes": ["110001"]
}
→ 200 OK
```

### 8️⃣ Get Feed (Requires Auth)
```
POST /get-feed/
Headers: Authorization: Bearer <access_token>
Body: {
  "lat": "28.6139",
  "long": "77.2090"
}
→ 200 OK
```

### 9️⃣ Refresh Token (No Auth)
```
POST /auth/token/refresh/
Body: {
  "refresh": "<refresh_token>"
}
→ 200 OK (returns new access_token)
```

---

## 📦 10 Available Interests
```
technology, art, travel, music, sports,
food, photography, fashion, fitness, diy
```

---

## ⚠️ Common Errors

| Code | Meaning | Solution |
|------|---------|----------|
| 400 | Bad Request | Check required fields |
| 401 | Unauthorized | Add/refresh token |
| 404 | Not Found | Check user exists |
| 500 | Server Error | Check backend logs |

---

## 🧪 Quick Test Commands

### Start Server
```bash
python manage.py runserver
```

### Run All Tests
```bash
python final_validation_test.py
```

### Test Single Endpoint (curl)
```bash
# Get Interests
curl -X POST http://127.0.0.1:8000/get-interests/ \
  -H "Content-Type: application/json" \
  -d '{"lat":"28.6139","long":"77.2090"}'

# Login
curl -X POST http://127.0.0.1:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email_id":"user@example.com","password":"Pass@123"}'

# Setup Profile (with token)
curl -X POST http://127.0.0.1:8000/setup-profile/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"name":"John Doe"}'
```

---

## 📚 Documentation Files

1. **POSTMAN_COLLECTION.md** - Complete Postman guide
2. **API_DOCUMENTATION.md** - Full API reference
3. **FINAL_IMPLEMENTATION_SUMMARY.md** - Technical overview
4. **Pinmate_API_Collection.postman_collection.json** - Import to Postman

---

## ✅ Quick Checklist

**Before Testing:**
- [ ] Server running (`python manage.py runserver`)
- [ ] Database migrated (`python manage.py migrate`)
- [ ] Interests populated (`python populate_interests.py`)
- [ ] Postman collection imported

**Testing Flow:**
1. [ ] Get Interests
2. [ ] Signup (Email or Phone)
3. [ ] Login (to get fresh tokens)
4. [ ] Setup Profile (with access_token)
5. [ ] Get Feed (with access_token)
6. [ ] Refresh Token (when needed)

---

## 🎯 Status: ✅ ALL 10 ENDPOINTS WORKING

Last Updated: December 10, 2025
