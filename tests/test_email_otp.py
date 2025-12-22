#!/usr/bin/env python
"""
Test script to send a real OTP email using Django's SMTP backend
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
import random


def generate_test_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))


def send_test_otp_email(recipient_email):
    """
    Send a test OTP email to verify SMTP configuration
    """
    otp = generate_test_otp()
    
    print(f"\n{'='*60}")
    print(f"📧 SENDING TEST OTP EMAIL")
    print(f"{'='*60}")
    print(f"To: {recipient_email}")
    print(f"From: {settings.DEFAULT_FROM_EMAIL}")
    print(f"SMTP Host: {settings.EMAIL_HOST}")
    print(f"SMTP Port: {settings.EMAIL_PORT}")
    print(f"OTP: {otp}")
    print(f"{'='*60}\n")
    
    try:
        result = send_mail(
            subject='Pinmate OTP Verification - Test',
            message=f'''Hello!

This is a test email from Pinmate OTP system.

Your verification code is: {otp}

This code is valid for 5 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Pinmate Team
''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
        print(f"✅ SUCCESS! Email sent successfully")
        print(f"   Result: {result} email(s) sent")
        print(f"\n📬 Check inbox: {recipient_email}")
        print(f"   OTP Code: {otp}\n")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to send email")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {str(e)}")
        print(f"\n💡 TROUBLESHOOTING:")
        print(f"   1. For Gmail, you need an App Password (not your regular password)")
        print(f"   2. Go to: https://myaccount.google.com/apppasswords")
        print(f"   3. Create an app password for 'Mail'")
        print(f"   4. Update EMAIL_HOST_PASSWORD in .env file")
        print(f"   5. Make sure 2-Step Verification is enabled on your Google account\n")
        return False


if __name__ == '__main__':
    recipient = 'rahuljha996886@gmail.com'
    
    print("\n🔐 Django SMTP Email OTP Test")
    print("=" * 60)
    
    # Check if email credentials are configured
    if not settings.EMAIL_HOST_PASSWORD or settings.EMAIL_HOST_PASSWORD == 'your_gmail_app_password_here':
        print("\n⚠️  WARNING: Email credentials not configured!")
        print(f"   Please update EMAIL_HOST_PASSWORD in .env file")
        print(f"\n   Using console backend for testing instead...\n")
        
        # Switch to console backend for testing
        settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
        send_test_otp_email(recipient)
        print("\n📋 Email content printed above (console backend)")
    else:
        # Try to send real email
        success = send_test_otp_email(recipient)
        
        if success:
            print("=" * 60)
            print("✅ TEST PASSED - OTP Email System Working!")
            print("=" * 60)
        else:
            print("=" * 60)
            print("❌ TEST FAILED - Check configuration above")
            print("=" * 60)
