# 📧 Gmail SMTP Setup for OTP Email Sending

## 🔐 Setup Gmail App Password

To send real OTP emails, you need to configure Gmail App Password:

### Step 1: Enable 2-Step Verification
1. Go to your Google Account: https://myaccount.google.com/
2. Click **Security** in the left sidebar
3. Under "How you sign in to Google", click **2-Step Verification**
4. Follow the steps to enable it

### Step 2: Generate App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select **Mail** as the app
3. Select **Other (Custom name)** as the device
4. Enter name: "Pinmate Backend"
5. Click **Generate**
6. Copy the 16-character password (no spaces)

### Step 3: Update .env File
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=rahuljha996886@gmail.com
EMAIL_HOST_PASSWORD=your_16_char_app_password_here
DEFAULT_FROM_EMAIL=Pinmate <rahuljha996886@gmail.com>
```

### Step 4: Test Email Sending
```bash
python test_email_otp.py
```

## 🧪 Test with Signup API

Once configured, test with curl:

```bash
# PROD mode - Real OTP will be sent to email
curl -X POST "http://127.0.0.1:8000/auth/signup/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: test-device" \
  -H "x-app-mode: prod" \
  -d '{
    "email_id": "rahuljha996886@gmail.com",
    "password": "TestPass123!",
    "lat": "28.6139",
    "long": "77.2090",
    "interests": [1, 2, 3],
    "debug": false
  }'

# Check your email for OTP code
# Then verify with:
curl -X POST "http://127.0.0.1:8000/auth/verify-otp/" \
  -H "Content-Type: application/json" \
  -H "x-device-id: test-device" \
  -H "x-app-mode: prod" \
  -d '{
    "identifier": "rahuljha996886@gmail.com",
    "entered_otp": "YOUR_OTP_FROM_EMAIL"
  }'
```

## 📝 Current Status

✅ Django SMTP configuration added
✅ Real email sending implemented with `send_mail()`
✅ OTP generation working (6-digit random)
✅ Email template created
⚠️ Gmail App Password needed for actual sending

## 🔄 Production Deployment (Render)

For production, add these environment variables in Render dashboard:

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=rahuljha996886@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password
DEFAULT_FROM_EMAIL=Pinmate <rahuljha996886@gmail.com>
```

## 🎯 Mode Matrix

| x-app-mode | debug | OTP Value | Email Sent | show_otp |
|------------|-------|-----------|------------|----------|
| prod       | false | Random 6-digit | ✅ YES | true |
| prod       | true  | ❌ Skipped | ❌ NO | false |
| staging    | false | 123456 | ❌ NO | true |
| staging    | true  | ❌ Skipped | ❌ NO | false |
