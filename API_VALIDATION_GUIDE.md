# 🛡️ Pinmate API - Input Validation Guide

## ✅ **Validation Features Implemented**

All API endpoints now include comprehensive input validation to ensure data integrity and security.

---

## 📋 **Validation Rules**

### **1. Phone Number Validation** 📱

**Requirements:**
- Must be exactly **10 digits**
- Must contain **only numeric characters**
- Special characters (spaces, hyphens, parentheses) are automatically removed during validation

**Validation Function:** `validate_phone_number(phone_number)`

**Examples:**
```python
✅ Valid:
- "9876543210"
- "9876543210" (cleaned from "98765-43210")
- "9876543210" (cleaned from "98 765 432 10")

❌ Invalid:
- "987654321"    → Error: "Phone number must be exactly 10 digits"
- "98765432101"  → Error: "Phone number must be exactly 10 digits"  
- "abcd123456"   → Error: "Phone number must contain only digits"
- ""             → Error: "Phone number is required"
```

**API Response:**
```json
{
  "error": "Phone number must be exactly 10 digits"
}
```

---

### **2. Coordinate Validation** 🌍

**Requirements:**
- **Latitude:** Must be between **-90** and **90**
- **Longitude:** Must be between **-180** and **180**
- Both must be **valid numeric values**

**Validation Function:** `validate_coordinates(lat, long)`

**Examples:**
```python
✅ Valid:
- lat: "28.613939", long: "77.209021"  (Delhi, India)
- lat: "-33.8688", long: "151.2093"    (Sydney, Australia)
- lat: "0", long: "0"                   (Atlantic Ocean)
- lat: "40.7128", long: "-74.0060"     (New York, USA)

❌ Invalid:
- lat: "91.5", long: "77.209021"       → Error: "Latitude must be between -90 and 90"
- lat: "28.613939", long: "200.5"      → Error: "Longitude must be between -180 and 180"
- lat: "invalid", long: "77.209021"    → Error: "Invalid coordinate format. Must be valid numbers"
- lat: "abc", long: "xyz"              → Error: "Invalid coordinate format. Must be valid numbers"
```

**API Response:**
```json
{
  "error": "Latitude must be between -90 and 90"
}
```

---

### **3. Pincode Validation** 📮

**Requirements:**
- Must be exactly **6 digits** (Indian pincode format)
- Must contain **only numeric characters**
- **Optional field** (validation only applies if pincode is provided)

**Validation Function:** `validate_pincode(pincode)`

**Examples:**
```python
✅ Valid:
- "110001"
- "560001"
- "400001"
- None or empty (optional field)

❌ Invalid:
- "1100"          → Error: "Pincode must be exactly 6 digits"
- "11000123"      → Error: "Pincode must be exactly 6 digits"
- "abcd12"        → Error: "Pincode must contain only digits"
```

**API Response:**
```json
{
  "error": "Invalid pincode from location: Pincode must be exactly 6 digits"
}
```

---

## 🔧 **Endpoints with Validation**

### **1. POST /auth/signup/**

**Validated Fields:**
- ✅ `number` - Phone number (10 digits, numeric)
- ✅ `lat` - Latitude (-90 to 90)
- ✅ `long` - Longitude (-180 to 180)
- ✅ `pincode` - From geocoded location (6 digits)

**Example Request:**
```json
{
  "number": "9876543210",
  "password": "Test@1234",
  "lat": "28.613939",
  "long": "77.209021",
  "interests": ["tech", "sports"]
}
```

**Validation Errors:**
```json
// Invalid phone
{
  "error": "Phone number must be exactly 10 digits"
}

// Invalid coordinates
{
  "error": "Latitude must be between -90 and 90"
}

// Invalid pincode from location
{
  "error": "Invalid pincode from location: Pincode must be exactly 6 digits"
}
```

---

### **2. POST /auth/login/**

**Validated Fields:**
- ✅ `number` - Phone number (10 digits, numeric)

**Example Request:**
```json
{
  "number": "9876543210",
  "password": "Test@1234"
}
```

**Validation Errors:**
```json
{
  "error": "Phone number must be exactly 10 digits"
}
```

---

### **3. POST /get-interests/**

**Validated Fields:**
- ✅ `lat` - Latitude (-90 to 90)
- ✅ `long` - Longitude (-180 to 180)

**Example Request:**
```json
{
  "lat": "28.613939",
  "long": "77.209021"
}
```

**Validation Errors:**
```json
{
  "error": "Longitude must be between -180 and 180"
}
```

---

### **4. POST /login/guest/**

**Validated Fields:**
- ✅ `lat` - Latitude (-90 to 90)
- ✅ `long` - Longitude (-180 to 180)
- ✅ `pincode` - From geocoded location (6 digits)

**Example Request:**
```json
{
  "interests": ["Art", "Travel"],
  "lat": "28.613939",
  "long": "77.209021"
}
```

**Validation Errors:**
```json
{
  "error": "Invalid coordinate format. Must be valid numbers"
}
```

---

### **5. POST /get-feed/**

**Validated Fields:**
- ✅ `lat` - Latitude (-90 to 90)
- ✅ `long` - Longitude (-180 to 180)

**Example Request:**
```json
{
  "lat": "28.613939",
  "long": "77.209021"
}
```

**Validation Errors:**
```json
{
  "error": "Latitude must be between -90 and 90"
}
```

---

## 🧪 **Testing Validation**

### **Test Invalid Phone Number**
```bash
# 9 digits (invalid)
curl -X POST http://127.0.0.1:8000/auth/signup/ \
  -H "Content-Type: application/json" \
  -H "Is-Debug: true" \
  -d '{"number": "987654321", "password": "Test@1234", "lat": "28.613939", "long": "77.209021"}'

# Response: {"error":"Phone number must be exactly 10 digits"}
```

### **Test Valid Phone Number**
```bash
# 10 digits (valid)
curl -X POST http://127.0.0.1:8000/auth/signup/ \
  -H "Content-Type: application/json" \
  -H "Is-Debug: true" \
  -d '{"number": "9876543210", "password": "Test@1234", "lat": "28.613939", "long": "77.209021"}'

# Response: Success with tokens
```

### **Test Invalid Latitude**
```bash
# Latitude > 90 (invalid)
curl -X POST http://127.0.0.1:8000/get-interests/ \
  -H "Content-Type: application/json" \
  -d '{"lat": "91.5", "long": "77.209021"}'

# Response: {"error":"Latitude must be between -90 and 90"}
```

### **Test Invalid Longitude**
```bash
# Longitude > 180 (invalid)
curl -X POST http://127.0.0.1:8000/get-interests/ \
  -H "Content-Type: application/json" \
  -d '{"lat": "28.613939", "long": "200.5"}'

# Response: {"error":"Longitude must be between -180 and 180"}
```

### **Test Non-Numeric Coordinates**
```bash
# Non-numeric values (invalid)
curl -X POST http://127.0.0.1:8000/get-interests/ \
  -H "Content-Type: application/json" \
  -d '{"lat": "invalid", "long": "77.209021"}'

# Response: {"error":"Invalid coordinate format. Must be valid numbers"}
```

---

## ✅ **Test Results**

All validation scenarios tested successfully:

| Test Case | Input | Expected Result | Status |
|-----------|-------|-----------------|--------|
| Valid phone (10 digits) | "9876543210" | ✅ Accepted | Pass |
| Invalid phone (9 digits) | "987654321" | ❌ Error: Must be 10 digits | Pass |
| Invalid phone (11 digits) | "98765432101" | ❌ Error: Must be 10 digits | Pass |
| Valid latitude | "28.613939" | ✅ Accepted | Pass |
| Invalid latitude (>90) | "91.5" | ❌ Error: Must be -90 to 90 | Pass |
| Invalid latitude (<-90) | "-95.0" | ❌ Error: Must be -90 to 90 | Pass |
| Valid longitude | "77.209021" | ✅ Accepted | Pass |
| Invalid longitude (>180) | "200.5" | ❌ Error: Must be -180 to 180 | Pass |
| Invalid longitude (<-180) | "-190.0" | ❌ Error: Must be -180 to 180 | Pass |
| Non-numeric coordinates | "invalid" | ❌ Error: Invalid format | Pass |
| Valid pincode | "110001" | ✅ Accepted | Pass |
| Invalid pincode (4 digits) | "1100" | ❌ Error: Must be 6 digits | Pass |

---

## 🔒 **Security Benefits**

### **Data Integrity**
- Prevents invalid phone numbers in database
- Ensures coordinates are within valid Earth ranges
- Maintains consistent pincode format

### **Error Prevention**
- Catches invalid inputs before processing
- Provides clear error messages to users
- Prevents geocoding API calls with invalid coordinates

### **User Experience**
- Immediate feedback on input errors
- Clear, actionable error messages
- Consistent validation across all endpoints

---

## 📚 **Implementation Details**

### **Validation Functions Location**
File: [api/auth_views.py](api/auth_views.py)

```python
# Phone number validation
def validate_phone_number(phone_number):
    """Validate 10-digit numeric phone number"""
    # Returns (is_valid, error_or_cleaned_number)

# Coordinate validation  
def validate_coordinates(lat, long):
    """Validate lat/long ranges"""
    # Returns (is_valid, error_message, lat_float, long_float)

# Pincode validation
def validate_pincode(pincode):
    """Validate 6-digit Indian pincode"""
    # Returns (is_valid, error_message, cleaned_pincode)
```

### **Integration**
All validations are called at the beginning of each endpoint handler before any database operations or external API calls.

---

## 🚀 **Production Recommendations**

1. **Rate Limiting:** Add rate limiting to prevent validation bypass attempts
2. **Logging:** Log validation failures for security monitoring
3. **Custom Error Codes:** Add specific error codes for each validation type
4. **Internationalization:** Support international phone formats (future)
5. **Advanced Pincode:** Validate against actual pincode database (optional)

---

**✅ All validation features implemented and tested successfully!**

Date: December 13, 2025
