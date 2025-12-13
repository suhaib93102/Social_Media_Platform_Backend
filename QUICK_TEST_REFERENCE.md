# 🚀 **PINMATE API - QUICK TEST REFERENCE**

## **Test Status: ✅ ALL ENDPOINTS WORKING**

| Endpoint | Method | URL | Auth Required | Status |
|----------|--------|-----|---------------|--------|
| **Email Login** | POST | `/auth/login/` | ❌ | ✅ Working |
| **Phone Login** | POST | `/auth/login/` | ❌ | ✅ Working |
| **Email Signup** | POST | `/auth/signup/` | ❌ | ✅ Working |
| **Phone Signup** | POST | `/auth/signup/` | ❌ | ✅ Working |
| **Get Interests** | POST | `/get-interests/` | ❌ | ✅ Working |
| **Guest Login** | POST | `/login/guest/` | ❌ | ✅ Working |
| **Get Feed** | POST | `/get-feed/` | ✅ | ✅ Working |
| **Setup Profile** | POST | `/setup-profile/` | ✅ | ✅ Working |
| **Token Refresh** | POST | `/auth/token/refresh/` | ❌ | ✅ Working |

---

## **🔑 Key Test Data**

### **Existing Test Users**
```json
{
  "email": "yathaarthbatra10@gmail.com",
  "password": "Yatha@1234",
  "phone": "7015926932"
}
```

### **Valid Coordinates (Bangalore)**
```json
{
  "lat": "12.9716",
  "long": "77.5946"
}
```

### **Sample Interests**
```json
["technology", "music", "travel", "sports", "art", "food"]
```

---

## **⚡ Quick Test Commands**

### **1. Start Server**
```bash
cd /Users/vishaljha/backend && python manage.py runserver
```

### **2. Test Email Login**
```bash
curl -X POST http://127.0.0.1:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email_id": "yathaarthbatra10@gmail.com", "password": "Yatha@1234"}'
```

### **3. Test Get Interests**
```bash
curl -X POST http://127.0.0.1:8000/get-interests/ \
  -H "Content-Type: application/json" \
  -d '{"lat": "12.9716", "long": "77.5946"}'
```

### **4. Test Guest Login**
```bash
curl -X POST http://127.0.0.1:8000/login/guest/ \
  -H "Content-Type: application/json" \
  -d '{"interests": ["technology", "music"], "lat": "12.9716", "long": "77.5946"}'
```

---

## **📋 Test Flow**

1. **Start Server** → `python manage.py runserver`
2. **Import Postman Collection** → `Pinmate_API_Collection.postman_collection.json`
3. **Set Environment** → `base_url = http://127.0.0.1:8000`
4. **Test Authentication** → Login/Signup endpoints
5. **Test Core Features** → Interests, Guest, Feed, Profile
6. **Verify Tokens** → Check environment variables update automatically

---

## **✅ Expected Results**

- **All endpoints**: Return 200/201 status codes
- **Authentication**: JWT tokens generated and saved
- **Location**: Geocoding works for valid coordinates
- **Data**: User profiles and interests properly stored
- **Errors**: Proper error messages for invalid inputs

---

## **🎯 Success Criteria Met**

✅ **9/9 endpoints functional**  
✅ **JWT authentication working**  
✅ **Geocoding service operational**  
✅ **Database operations successful**  
✅ **Error handling implemented**  
✅ **Postman collection ready**  

**🚀 Pinmate API is production-ready!**