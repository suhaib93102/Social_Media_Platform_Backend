#!/bin/bash

# Quick Email Test Script
# Run this after updating EMAIL_HOST_PASSWORD in .env

echo "🧪 Testing Gmail SMTP with your credentials..."
echo ""

cd /Users/vishaljha/backend

python << 'PYCODE'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from django.core.mail import send_mail
from django.conf import settings
import random

print("="*70)
print("📧 Gmail SMTP Configuration:")
print("="*70)
print(f"Host: {settings.EMAIL_HOST}")
print(f"Port: {settings.EMAIL_PORT}")
print(f"User: {settings.EMAIL_HOST_USER}")
print(f"Password: {'✅ SET' if settings.EMAIL_HOST_PASSWORD and settings.EMAIL_HOST_PASSWORD != 'your_gmail_app_password_here' else '❌ NOT SET'}")
print("="*70)

if not settings.EMAIL_HOST_PASSWORD or settings.EMAIL_HOST_PASSWORD == 'your_gmail_app_password_here':
    print("\n❌ ERROR: Gmail App Password not configured!")
    print("\n👉 Visit: https://myaccount.google.com/apppasswords")
    print("👉 Generate password and update .env file")
    print("👉 Then run this test again")
    exit(1)

print("\n📨 Sending test OTP email...")

otp = str(random.randint(100000, 999999))
email = "rahul22389@iiitd.ac.in"

try:
    send_mail(
        subject="Pinmate OTP Verification - Test",
        message=f"""Hello!

This is a TEST email from Pinmate.

Your OTP code is: {otp}

If you received this, email sending is working! 🎉

Best regards,
Pinmate Team
""",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
    
    print(f"\n✅ SUCCESS! Email sent to {email}")
    print(f"📬 CHECK YOUR INBOX NOW!")
    print(f"🔑 Test OTP: {otp}")
    print("\n🎉 Gmail SMTP is working correctly!")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    print("\n💡 Troubleshooting:")
    print("   1. Make sure you generated an App Password (not your Gmail password)")
    print("   2. Visit: https://myaccount.google.com/apppasswords")
    print("   3. Remove spaces from the password in .env")
    print("   4. Enable 2-Step Verification if not already enabled")
    print("="*70)
    exit(1)

PYCODE
