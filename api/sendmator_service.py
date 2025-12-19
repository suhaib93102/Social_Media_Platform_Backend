"""
Sendmator OTP Service Integration
Handles sending and verifying OTPs via Sendmator API
"""
import requests
from django.conf import settings
import os


class SendmatorService:
    """Service class for Sendmator OTP operations"""
    
    BASE_URL = "https://api.sendmator.com/api/v1/otp"
    
    @staticmethod
    def get_api_key():
        """Get Sendmator API key from environment"""
        return os.getenv('SENDMATOR_API_KEY', settings.SENDMATOR_API_KEY if hasattr(settings, 'SENDMATOR_API_KEY') else None)
    
    @staticmethod
    def send_otp_email(email, sandbox_mode=False):
        """
        Send OTP via email using Sendmator
        
        Args:
            email: Recipient email address
            sandbox_mode: If True, uses sandbox mode (returns OTP without sending)
        
        Returns:
            tuple: (success: bool, session_token: str|None, otp: str|None, error: str|None)
        """
        api_key = SendmatorService.get_api_key()
        if not api_key:
            print("❌ SENDMATOR_API_KEY not configured")
            return (False, None, None, "Sendmator API key not configured")
        
        url = f"{SendmatorService.BASE_URL}/send"
        headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "channels": ["email"],
            "recipients": {
                "email": email
            },
            "metadata": {
                "purpose": "pinmate_verification"
            }
        }
        
        # Add sandbox mode if enabled
        if sandbox_mode:
            payload["sandbox_mode"] = True
        
        try:
            print(f"\n{'='*60}")
            print(f"📧 SENDMATOR: Sending OTP Email")
            print(f"{'='*60}")
            print(f"To: {email}")
            print(f"Sandbox: {sandbox_mode}")
            print(f"{'='*60}\n")
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                session_token = data.get('session_token')
                
                # In sandbox mode, get the OTP from response
                sandbox_otp = None
                if sandbox_mode and 'sandbox_otps' in data:
                    sandbox_otp = data['sandbox_otps'].get('email')
                    print(f"🔑 SANDBOX OTP: {sandbox_otp}")
                
                print(f"✅ SENDMATOR: OTP sent successfully")
                print(f"Session Token: {session_token[:50]}...")
                
                return (True, session_token, sandbox_otp, None)
            else:
                error_msg = f"Sendmator API error: {response.status_code} - {response.text}"
                print(f"❌ SENDMATOR ERROR: {error_msg}")
                return (False, None, None, error_msg)
                
        except Exception as e:
            error_msg = f"Sendmator request failed: {type(e).__name__}: {e}"
            print(f"❌ SENDMATOR EXCEPTION: {error_msg}")
            return (False, None, None, error_msg)
    
    @staticmethod
    def send_otp_sms(phone, sandbox_mode=False):
        """
        Send OTP via SMS using Sendmator
        
        Args:
            phone: Recipient phone number (with country code)
            sandbox_mode: If True, uses sandbox mode
        
        Returns:
            tuple: (success: bool, session_token: str|None, otp: str|None, error: str|None)
        """
        api_key = SendmatorService.get_api_key()
        if not api_key:
            print("❌ SENDMATOR_API_KEY not configured")
            return (False, None, None, "Sendmator API key not configured")
        
        # Format phone number with country code if not present
        if not phone.startswith('+'):
            phone = f"+91{phone}"  # Default to India country code
        
        url = f"{SendmatorService.BASE_URL}/send"
        headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "channels": ["sms"],
            "recipients": {
                "sms": phone
            },
            "metadata": {
                "purpose": "pinmate_verification"
            }
        }
        
        # Add sandbox mode if enabled
        if sandbox_mode:
            payload["sandbox_mode"] = True
        
        try:
            print(f"\n{'='*60}")
            print(f"📱 SENDMATOR: Sending OTP SMS")
            print(f"{'='*60}")
            print(f"To: {phone}")
            print(f"Sandbox: {sandbox_mode}")
            print(f"{'='*60}\n")
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                session_token = data.get('session_token')
                
                # In sandbox mode, get the OTP from response
                sandbox_otp = None
                if sandbox_mode and 'sandbox_otps' in data:
                    sandbox_otp = data['sandbox_otps'].get('sms')
                    print(f"🔑 SANDBOX OTP: {sandbox_otp}")
                
                print(f"✅ SENDMATOR: SMS OTP sent successfully")
                print(f"Session Token: {session_token[:50]}...")
                
                return (True, session_token, sandbox_otp, None)
            else:
                error_msg = f"Sendmator API error: {response.status_code} - {response.text}"
                print(f"❌ SENDMATOR ERROR: {error_msg}")
                return (False, None, None, error_msg)
                
        except Exception as e:
            error_msg = f"Sendmator request failed: {type(e).__name__}: {e}"
            print(f"❌ SENDMATOR EXCEPTION: {error_msg}")
            return (False, None, None, error_msg)
    
    @staticmethod
    def verify_otp(session_token, otp_code, channel_type='email'):
        """
        Verify OTP using Sendmator
        
        Args:
            session_token: Session token from send_otp response
            otp_code: OTP code entered by user
            channel_type: 'email' or 'sms'
        
        Returns:
            tuple: (verified: bool, attempts_remaining: int|None, error: str|None)
        """
        api_key = SendmatorService.get_api_key()
        if not api_key:
            return (False, None, "Sendmator API key not configured")
        
        url = f"{SendmatorService.BASE_URL}/verify"
        headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "session_token": session_token,
            "otps": {
                channel_type: str(otp_code)
            }
        }
        
        try:
            print(f"\n{'='*60}")
            print(f"🔍 SENDMATOR: Verifying OTP")
            print(f"{'='*60}")
            print(f"Channel: {channel_type}")
            print(f"OTP: {otp_code}")
            print(f"{'='*60}\n")
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                verified = data.get('verified', False)
                session_verified = data.get('session_verified', False)
                attempts_remaining = data.get('attempts_remaining')
                
                if verified and session_verified:
                    print(f"✅ SENDMATOR: OTP verified successfully")
                    return (True, attempts_remaining, None)
                else:
                    print(f"❌ SENDMATOR: OTP verification failed")
                    return (False, attempts_remaining, "Invalid OTP")
            else:
                try:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                    error_msg = error_data.get('error') or error_data.get('message', f"Verification failed: {response.status_code}")
                    print(f"❌ SENDMATOR ERROR: {error_msg}")
                    print(f"Response: {response.text}")
                    return (False, None, error_msg)
                except:
                    print(f"❌ SENDMATOR ERROR: {response.status_code} - {response.text}")
                    return (False, None, f"Verification failed: {response.status_code}")
                
        except Exception as e:
            error_msg = f"Verification request failed: {type(e).__name__}: {e}"
            print(f"❌ SENDMATOR EXCEPTION: {error_msg}")
            return (False, None, error_msg)
