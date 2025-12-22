from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import check_password, make_password
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from .models import UserProfile, Interest, OTPVerification, PendingSignup
from .serializers import UserProfileSerializer, InterestSerializer
from .headers_util import (
    get_headers, get_or_create_guest_user, is_debug_mode,
    get_otp_for_debug_mode, verify_otp_in_debug_or_production,
    get_otp_message
)
from .sendmator_service import SendmatorService
import uuid
import requests
import random
import re
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import os
import socket
import smtplib
import ssl


def validate_phone_number(phone_number):
    """
    Validate phone number - must be 10 digits and numeric only
    Returns (is_valid, error_message)
    """
    if not phone_number:
        return False, "Phone number is required"
    
    # Remove any spaces or special characters
    cleaned_number = re.sub(r'[^\d]', '', phone_number)
    
    # Check if it's exactly 10 digits
    if len(cleaned_number) != 10:
        return False, "Phone number must be exactly 10 digits"
    
    # Check if it's all numeric
    if not cleaned_number.isdigit():
        return False, "Phone number must contain only digits"
    
    return True, cleaned_number


def validate_coordinates(lat, long):
    """
    Validate latitude and longitude coordinates
    Returns (is_valid, error_message, lat_float, long_float)
    """
    try:
        lat_float = float(lat)
        long_float = float(long)
        
        # Check if coordinates are in valid range
        if not (-90 <= lat_float <= 90):
            return False, "Latitude must be between -90 and 90", None, None
        
        if not (-180 <= long_float <= 180):
            return False, "Longitude must be between -180 and 180", None, None
        
        return True, None, lat_float, long_float
        
    except (ValueError, TypeError):
        return False, "Invalid coordinate format. Must be valid numbers", None, None


def validate_pincode(pincode):
    """
    Validate pincode - must be 6 digits for India
    Returns (is_valid, error_message, cleaned_pincode)
    """
    if not pincode:
        return True, None, None  # Pincode is optional
    
    # Remove any spaces or special characters
    cleaned_pincode = re.sub(r'[^\d]', '', str(pincode))
    
    # Check if it's exactly 6 digits (Indian pincode format)
    if len(cleaned_pincode) != 6:
        return False, "Pincode must be exactly 6 digits", None
    
    # Check if it's all numeric
    if not cleaned_pincode.isdigit():
        return False, "Pincode must contain only digits", None
    
    return True, None, cleaned_pincode


def generate_otp():
    """Generate a 6-digit OTP code"""
    return str(random.randint(100000, 999999))


def send_email_otp(email, otp):
    """
    Send OTP via email using Django SMTP backend
    REAL EMAIL SENDING for production
    Returns: (success: bool, otp: str)
    """
    # Quick config check — if SMTP credentials aren't set, skip trying to send
    if not getattr(settings, 'EMAIL_HOST_PASSWORD', None) or settings.EMAIL_HOST_PASSWORD == 'your_gmail_app_password_here':
        print("❌ [EMAIL CONFIG] EMAIL_HOST_PASSWORD not set or invalid. Skipping send_mail.")
        print(f"⚠️  Email not sent, but OTP is still valid: {otp}")
        # Provide OTP in response for safe testing (production should not expose OTP)
        return (False, otp)

    # Send email asynchronously to avoid blocking gunicorn worker and possible timeouts
    try:
        print(f"\n{'='*60}")
        print(f"📧 SCHEDULING OTP EMAIL (background send)")
        print(f"{'='*60}")
        print(f"To: {email}")
        print(f"OTP: {otp}")
        print(f"From: {settings.DEFAULT_FROM_EMAIL}")
        print(f"SMTP: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        print(f"{'='*60}\n")

        import threading

        def _send():
            try:
                send_mail(
                    subject="Pinmate OTP Verification",
                    message=f"Your Pinmate OTP is {otp}. It is valid for 5 minutes.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                print(f"✅ [OTP EMAIL SENT] Successfully sent OTP to {email}")
                print(f"📬 CHECK YOUR INBOX: {email}")
                print(f"🔑 OTP CODE: {otp}\n")
            except Exception as e:
                print(f"❌ [EMAIL ERROR - BACKGROUND] Failed to send OTP email: {type(e).__name__}: {e}")
                print("⚠️  Email sending failed in background; OTP remains valid in DB.")

        t = threading.Thread(target=_send, daemon=True)
        t.start()

        # We scheduled the send; return True to indicate email send was initiated
        return (True, otp)

    except Exception as e:
        # If scheduling itself fails, fallback safely
        print(f"❌ [EMAIL SCHEDULING ERROR] {type(e).__name__}: {e}")
        return (False, otp)


def send_otp_sms(phone_number, otp_code):
    """
    Send OTP via SMS
    For production, integrate with SMS service (Twilio, AWS SNS, etc.)
    """
    try:
        print(f"\n{'='*60}")
        print(f"📱 ATTEMPTING TO SEND OTP SMS")
        print(f"{'='*60}")
        print(f"To: {phone_number}")
        print(f"OTP: {otp_code}")
        print(f"{'='*60}\n")
        
        # TODO: Implement actual SMS sending
        # For now, just print to console (development mode)
        print(f"[OTP SMS] OTP code for {phone_number}: {otp_code}")
        print(f"SMS would be sent: 'Your Pinmate verification code is: {otp_code}. Valid for 5 minutes.'")
        print(f"⚠️  SMS sending not implemented - OTP printed above\n")
        return True
    except Exception as e:
        print(f"Error sending SMS OTP: {e}")
        return False


def handle_otp(identifier, is_email, app_mode, debug, force_sendmator=False, skip_otp=False):
    """
    Core OTP logic handler using Sendmator:
    - prod + debug=false: Sendmator real OTP (if force_sendmator=True) or Gmail SMTP
    - prod + debug=true: Skip OTP
    - staging + debug=false: Sendmator sandbox mode
    - staging + debug=true: Skip OTP
    - skip_otp=true: Skip OTP regardless of debug mode
    
    Returns: {
        "show_otp": bool, 
        "otp": str/None, 
        "session_token": str/None,
        "sendmator_used": bool
    }
    """
    # SKIP OTP → Skip OTP regardless of debug mode
    if skip_otp:
        return {
            "show_otp": False,
            "otp": None,
            "session_token": None,
            "sendmator_used": False
        }
    
    # DEBUG → Skip OTP
    if debug:
        return {
            "show_otp": False,
            "otp": None,
            "session_token": None,
            "sendmator_used": False
        }
    
    # Determine if we should use sandbox mode
    sandbox_mode = (app_mode == "staging")
    
    # Check if Sendmator is forced via request parameter
    if force_sendmator:
        # Force Sendmator usage regardless of app_mode
        if is_email:
            success, session_token, otp, error = SendmatorService.send_otp_email(
                identifier, 
                sandbox_mode=False  # Force production mode when explicitly requested
            )
        else:
            success, session_token, otp, error = SendmatorService.send_otp_sms(
                identifier, 
                sandbox_mode=False
            )
    elif sandbox_mode:
        # Use Sendmator for sandbox testing
        if is_email:
            success, session_token, otp, error = SendmatorService.send_otp_email(
                identifier, 
                sandbox_mode=sandbox_mode
            )
        else:
            success, session_token, otp, error = SendmatorService.send_otp_sms(
                identifier, 
                sandbox_mode=sandbox_mode
            )
    else:
        # Production mode: Use Gmail SMTP for now (Sendmator not configured)
        print(f"📧 Using Gmail SMTP for production email to {identifier}")
        otp = generate_otp()
        
        if is_email:
            email_sent, otp = send_email_otp(identifier, otp)
            success = email_sent
            error = None if email_sent else "Gmail SMTP send failed"
        else:
            send_otp_sms(identifier, otp)
            success = True
            error = None
        
        session_token = None  # No Sendmator token in SMTP mode
    
    if success:
        return {
            "show_otp": True,
            "otp": otp if sandbox_mode or force_sendmator else None,  # Only expose OTP in sandbox mode or when forced
            "otp_for_storage": otp,  # Always include OTP for database storage
            "session_token": session_token,
            "sendmator_used": True if force_sendmator or sandbox_mode else False,
            "error": None
        }
    else:
        # Fallback to old method if Sendmator fails
        print(f"⚠️ Sendmator failed, using fallback method: {error}")
        otp = generate_otp()
        email_sent = False
        
        if is_email:
            email_sent, otp = send_email_otp(identifier, otp)
        else:
            send_otp_sms(identifier, otp)
        
        return {
            "show_otp": True,
            "otp": otp,
            "otp_for_storage": otp,
            "session_token": None,
            "sendmator_used": False,
            "email_sent": email_sent,
            "error": error
        }


def create_otp_record(identifier, otp_code, session_token=None):
    """Create OTP verification record"""
    expires_at = timezone.now() + timedelta(minutes=10)
    OTPVerification.objects.create(
        identifier=identifier,
        otp_code=otp_code,
        expires_at=expires_at,
        session_token=session_token
    )


def get_location_details(lat, long):
    """
    Get location details (pincode, city, state, country) from coordinates.
    Uses Google Maps Geocoding API
    """
    try:
        # Basic coordinate validation
        lat_float = float(lat)
        long_float = float(long)

        # Check if coordinates are in valid range
        if not (-90 <= lat_float <= 90) or not (-180 <= long_float <= 180):
            print(f"Invalid coordinates: lat={lat}, long={long}")
            return {
                'pincode': '000000',
                'city': 'Invalid Coordinates',
                'state': 'Invalid Coordinates',
                'country': 'Invalid Coordinates'
            }

        # Use Google Maps Geocoding API
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{long}&key={settings.GOOGLE_MAPS_API_KEY}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Check if geocoding was successful
            if data.get('status') != 'OK':
                print(f"Google Geocoding API error: {data.get('status')}")
                return {
                    'pincode': '000000',
                    'city': 'Location Not Found',
                    'state': 'Location Not Found',
                    'country': 'Location Not Found'
                }

            # Get the first result
            if not data.get('results'):
                print("No geocoding results found")
                return {
                    'pincode': '000000',
                    'city': 'Location Not Found',
                    'state': 'Location Not Found',
                    'country': 'Location Not Found'
                }

            result = data['results'][0]
            address_components = result.get('address_components', [])

            # Parse address components
            location_data = {
                'pincode': '000000',
                'city': 'Unknown',
                'state': 'Unknown',
                'country': 'Unknown'
            }

            for component in address_components:
                types = component.get('types', [])
                long_name = component.get('long_name', '')

                if 'postal_code' in types:
                    location_data['pincode'] = long_name
                elif 'locality' in types:
                    location_data['city'] = long_name
                elif 'administrative_area_level_1' in types:
                    location_data['state'] = long_name
                elif 'country' in types:
                    location_data['country'] = long_name

            # Fallback for city if locality not found
            if location_data['city'] == 'Unknown':
                for component in address_components:
                    types = component.get('types', [])
                    if 'administrative_area_level_2' in types:
                        location_data['city'] = component.get('long_name', 'Unknown')
                        break

            return location_data
        else:
            print(f"Google Geocoding API returned status {response.status_code}")

    except ValueError as e:
        print(f"Invalid coordinate format: {e}")
        return {
            'pincode': '000000',
            'city': 'Invalid Format',
            'state': 'Invalid Format',
            'country': 'Invalid Format'
        }
    except Exception as e:
        print(f"Geocoding error: {e}")

    # Default fallback
    return {
        'pincode': '000000',
        'city': 'Unknown',
        'state': 'Unknown',
        'country': 'Unknown'
    }


class SignupView(APIView):
    """
    POST /auth/signup/
    Create a new user account with email_id or number
    With OTP verification support
    
    Headers (Required):
    - x-device-id: Unique device identifier
    - x-app-mode: 'debug' or 'release'
    
    Request: 
    {
        "email_id": "...", 
        "password": "...", 
        "lat": "...", 
        "long": "...", 
        "interests": [...],
        "debug": true/false (optional, overrides environment-based debug mode)
    }
    or
    {
        "number": "...", 
        "password": "...", 
        "lat": "...", 
        "long": "...", 
        "interests": [...],
        "debug": true/false (optional)
    }
    
    Debug Mode Behavior:
    - If debug=true OR (NODE_ENV=development AND x-app-mode=debug):
      * User created immediately without OTP verification
      * No SMS/Email sent
      * Returns tokens and user data
    - Otherwise:
      * Sends real OTP via SMS/Email
      * Requires OTP verification via /auth/verify-otp/
    """
    def post(self, request):
        # Get and validate headers
        device_id, app_mode, _, headers_valid, headers_error = get_headers(request)
        if not headers_valid:
            return Response({'error': headers_error}, status=status.HTTP_400_BAD_REQUEST)
        
        email_id = request.data.get('email_id')
        number = request.data.get('number')
        password = request.data.get('password')
        lat = request.data.get('lat')
        long = request.data.get('long')
        interests = request.data.get('interests', [])
        
        # Debug parameter - support both header and body
        debug_header = request.headers.get('debug', 'false').lower() == 'true'
        debug_body = request.data.get('debug', False)
        debug = debug_header or bool(debug_body)
        
        # Skip OTP parameter - force direct profile creation
        skip_otp = request.data.get('skip_otp', False)
        
        # Sendmator parameter - force Sendmator usage if specified
        force_sendmator = request.data.get('sendmator', False)
        
        # Validate input
        if not password:
            return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not email_id and not number:
            return Response({'error': 'Either email_id or number is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not lat or not long:
            return Response({'error': 'Location (lat, long) is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate phone number if provided
        if number:
            is_valid, phone_result = validate_phone_number(number)
            if not is_valid:
                return Response({'error': phone_result}, status=status.HTTP_400_BAD_REQUEST)
            number = phone_result  # Use cleaned phone number
        
        # Validate coordinates
        coords_valid, coords_error, lat_float, long_float = validate_coordinates(lat, long)
        if not coords_valid:
            return Response({'error': coords_error}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get location details from coordinates
        location_details = get_location_details(lat, long)
        
        # Validate pincode from location details
        pincode_valid, pincode_error, cleaned_pincode = validate_pincode(location_details.get('pincode'))
        if not pincode_valid:
            return Response({'error': f"Invalid pincode from location: {pincode_error}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Use cleaned pincode if valid, otherwise use original
        if cleaned_pincode:
            location_details['pincode'] = cleaned_pincode
        
        # Generate userId from email or phone (normalize emails)
        if email_id:
            email_id = email_id.strip().lower()
            user_id = email_id.split('@')[0]
            identifier = email_id
        else:
            user_id = f"user_{number}"
            identifier = number
        
        if email_id and UserProfile.objects.filter(email=email_id).exists():
            return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)
        
        if number and UserProfile.objects.filter(phone_number=number).exists():
            return Response({'error': 'Phone number already registered'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Hash password
        hashed_password = make_password(password)
        
        # Store pending signup data with device_id
        PendingSignup.objects.filter(identifier=identifier).delete()  # Remove old pending signups
        pending = PendingSignup.objects.create(
            identifier=identifier,
            email=email_id,
            phone_number=number,
            password=hashed_password,
            latitude=float(lat),
            longitude=float(long),
            interests=interests,
            pincode=location_details['pincode'],
            city=location_details['city'],
            state=location_details['state'],
            country=location_details['country'],
            device_id=device_id
        )
        
        # Handle OTP using the new core logic
        try:
            otp_result = handle_otp(
                identifier=identifier,
                is_email=bool(email_id),
                app_mode=app_mode,
                debug=debug,
                force_sendmator=force_sendmator,
                skip_otp=skip_otp
            )
        except Exception as e:
            import traceback
            print(f"\n{'='*60}")
            print(f"ERROR IN handle_otp:")
            print(traceback.format_exc())
            print(f"{'='*60}\n")
            return Response({'error': f'OTP service error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # If OTP is required, store it and return
        if otp_result.get("otp_for_storage") or otp_result.get("session_token"):
            # ... existing OTP storage code ...
            try:
                # Delete old OTP codes for this identifier
                OTPVerification.objects.filter(identifier=identifier).delete()
                
                # Create new OTP record with 10-minute expiry (Sendmator default)
                expires_at = timezone.now() + timedelta(minutes=10)
                
                # Store OTP code - use otp_for_storage which always has the OTP value
                # In sandbox mode: otp_for_storage contains the OTP (same as otp)
                # In production mode: otp_for_storage contains the OTP (otp is None for security)
                otp_code = otp_result.get("otp_for_storage") or otp_result.get("otp") or "000000"
                session_token = otp_result.get("session_token")
                
                OTPVerification.objects.create(
                    identifier=identifier,
                    otp_code=otp_code,
                    expires_at=expires_at,
                    session_token=session_token
                )
                
                # For development/debugging: Print OTP to console
                if otp_result.get("otp"):
                    print(f"\n{'🔑 '*30}")
                    print(f"OTP FOR {identifier}: {otp_result['otp']}")
                    print(f"{'🔑 '*30}\n")
                
                # Check if using Sendmator
                sendmator_used = otp_result.get('sendmator_used', False)
                
                response_data = {
                    'show_otp': otp_result.get("show_otp", True),
                    'message': 'OTP sent via Sendmator' if sendmator_used else 'OTP sent successfully',
                    'identifier': identifier,
                    'sendmator': sendmator_used
                }
                
                # Include OTP in sandbox/staging mode or if email failed
                if otp_result.get("otp"):
                    response_data['otp'] = otp_result['otp']
                
                # If Sendmator failed or email failed to send
                if otp_result.get('error'):
                    response_data['note'] = f"Fallback mode: {otp_result['error']}"
                
                email_sent = otp_result.get('email_sent', True)
                if not email_sent and not sendmator_used:
                    if otp_result.get("otp"):
                        response_data['otp'] = otp_result["otp"]
                    response_data['note'] = 'Email sending failed - OTP included in response. Configure EMAIL_HOST_PASSWORD.'
                
                return Response(response_data, status=status.HTTP_200_OK)
            except Exception as e:
                import traceback
                print(f"\n{'='*60}")
                print(f"ERROR IN SIGNUP OTP STORAGE:")
                print(traceback.format_exc())
                print(f"{'='*60}\n")
                return Response({'error': f'Signup error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Debug mode: Skip OTP and create user immediately
        if not otp_result.get("show_otp", True):
            # Debug mode: check for existing guest user to upgrade
            guest_user = None
            if device_id:
                try:
                    guest_user = UserProfile.objects.get(device_id=device_id, is_guest=True)
                except UserProfile.DoesNotExist:
                    pass
            
            if guest_user:
                # Upgrade guest to user: update existing record
                guest_user.userId = user_id
                guest_user.email = email_id
                guest_user.phone_number = number
                guest_user.password = hashed_password
                guest_user.latitude = float(lat)
                guest_user.longitude = float(long)
                guest_user.interests = interests
                guest_user.pincode = location_details['pincode']
                guest_user.city = location_details['city']
                guest_user.state = location_details['state']
                guest_user.country = location_details['country']
                guest_user.is_guest = False
                guest_user.save()
                user = guest_user
                
                # Clean up pending signup
                pending.delete()
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'debug': False,
                    'message': 'Guest upgraded to user successfully (debug mode)',
                    'user_role': 'user',
                    'user': {
                        'userId': user.userId,
                        'name': user.name,
                        'email': user.email
                    },
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token)
                    }
                }, status=status.HTTP_200_OK)
            else:
                # Create new user
                user_data = {
                    'userId': user_id,
                    'email': email_id,
                    'phone_number': number,
                    'password': password,
                    'latitude': float(lat),
                    'longitude': float(long),
                    'interests': interests,
                    'pincode': location_details['pincode'],
                    'city': location_details['city'],
                    'state': location_details['state'],
                    'country': location_details['country'],
                    'device_id': device_id,
                    'is_guest': False
                }
                
                serializer = UserProfileSerializer(data=user_data)
                if serializer.is_valid():
                    user = serializer.save()
                    
                    # Generate JWT tokens
                    refresh = RefreshToken.for_user(user)
                    
                    # Clean up pending signup
                    pending.delete()
                    
                    return Response({
                        'debug': False,
                        'message': 'User created successfully (debug mode)',
                        'user_role': 'user',
                        'user': {
                            'userId': user.userId,
                            'name': user.name,
                            'email': user.email
                        },
                        'tokens': {
                            'refresh': str(refresh),
                            'access': str(refresh.access_token)
                        }
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({'error': f'Validation error: {serializer.errors}'}, status=status.HTTP_400_BAD_REQUEST)
                
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST /auth/login/
    Login with email_id or number and password
    Request: {"email_id": "...", "password": "..."}
    or {"number": "...", "password": "..."}
    """
    def post(self, request):
        email_id = request.data.get('email_id')
        number = request.data.get('number')
        password = request.data.get('password')
        
        if not password:
            return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not email_id and not number:
            return Response({'error': 'Either email_id or number is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate phone number if provided
        if number:
            is_valid, phone_result = validate_phone_number(number)
            if not is_valid:
                return Response({'error': phone_result}, status=status.HTTP_400_BAD_REQUEST)
            number = phone_result  # Use cleaned phone number
        
        # Try to find user by email or phone
        try:
            if email_id:
                user = UserProfile.objects.get(email=email_id)
            else:
                user = UserProfile.objects.get(phone_number=number)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Verify password
        if not user.password or not check_password(password, user.password):
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Login successful',
            'user': {
                'userId': user.userId,
                'name': user.name,
                'email': user.email,
                'bio': user.bio,
                'profilePhoto': user.profilePhoto
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        }, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    """
    POST /auth/verify-otp/
    Verify OTP and complete user registration
    
    Headers (Required):
    - x-device-id: Unique device identifier
    - x-app-mode: 'debug' or 'release'
    
    Request: {
        "identifier": "email or phone", 
        "entered_otp": "123456"
    }
    
    Behavior:
    - Debug mode: accepts fixed OTP '123456'
    - Production mode: verifies actual OTP
    - If device_id has guest user: upgrades guest to real user
    - Otherwise: creates new user
    """
    def post(self, request):
        # Get and validate headers
        device_id, app_mode, _, headers_valid, headers_error = get_headers(request)
        if not headers_valid:
            return Response({'error': headers_error}, status=status.HTTP_400_BAD_REQUEST)
        
        identifier = request.data.get('identifier')
        entered_otp = request.data.get('entered_otp')
        
        # Debug parameter - support both header and body
        debug_header = request.headers.get('debug', 'false').lower() == 'true'
        debug_body = request.data.get('debug', False)
        debug = debug_header or bool(debug_body)
        
        if not identifier:
            return Response({'error': 'Identifier is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Normalize and validate identifier (email or phone)
        if '@' in identifier:
            identifier = identifier.strip().lower()
        else:
            is_valid, phone_result = validate_phone_number(identifier)
            if not is_valid:
                return Response({'error': phone_result}, status=status.HTTP_400_BAD_REQUEST)
            identifier = phone_result
        
        # Handle OTP verification based on mode
        if debug:
            # DEBUG → Skip OTP verification entirely
            pass
        else:
            # Get OTP record
            if not entered_otp:
                return Response({'error': 'OTP is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            otp_record = OTPVerification.objects.filter(
                identifier=identifier,
                is_verified=False
            ).order_by('-created_at').first()
            
            if not otp_record:
                return Response({'error': 'No OTP found. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if OTP is expired
            if otp_record.is_expired():
                return Response({'error': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Determine channel type
            channel_type = 'email' if '@' in identifier else 'sms'
            
            # If Sendmator session token exists, use Sendmator verification
            if otp_record.session_token:
                print(f"🔍 Using Sendmator verification for {identifier}")
                verified, attempts_remaining, error = SendmatorService.verify_otp(
                    session_token=otp_record.session_token,
                    otp_code=entered_otp,
                    channel_type=channel_type
                )
                
                if not verified:
                    error_msg = error or 'Invalid OTP'
                    if attempts_remaining is not None and attempts_remaining > 0:
                        error_msg += f'. {attempts_remaining} attempts remaining.'
                    return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
                
                print(f"✅ Sendmator verification successful")
            else:
                # Fallback: Local OTP verification
                print(f"🔍 Using local verification for {identifier}")
                if app_mode == "staging":
                    # STAGING → Verify against default OTP "123456"
                    if str(entered_otp) != '123456':
                        return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Verify against stored OTP
                    if otp_record.otp_code != str(entered_otp):
                        return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark OTP as verified
            otp_record.is_verified = True
            otp_record.save()
        
        # Get pending signup data
        try:
            pending_signup = PendingSignup.objects.get(identifier=identifier)
        except PendingSignup.DoesNotExist:
            return Response({'error': 'Signup data not found. Please start signup again.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate userId
        if pending_signup.email:
            user_id = pending_signup.email.split('@')[0]
        else:
            user_id = f"user_{pending_signup.phone_number}"
        
        # Check if guest user exists with this device_id
        guest_user = None
        if device_id:
            try:
                guest_user = UserProfile.objects.get(device_id=device_id, is_guest=True)
            except UserProfile.DoesNotExist:
                pass
        
        if guest_user:
            # Upgrade guest to user: update existing record
            guest_user.userId = user_id
            guest_user.email = pending_signup.email
            guest_user.phone_number = pending_signup.phone_number
            guest_user.password = pending_signup.password
            guest_user.latitude = pending_signup.latitude
            guest_user.longitude = pending_signup.longitude
            guest_user.interests = pending_signup.interests
            guest_user.pincode = pending_signup.pincode
            guest_user.city = pending_signup.city
            guest_user.state = pending_signup.state
            guest_user.country = pending_signup.country
            guest_user.is_guest = False
            guest_user.save()
            user = guest_user
        else:
            # Create new user
            user_data = {
                'userId': user_id,
                'email': pending_signup.email,
                'phone_number': pending_signup.phone_number,
                'password': pending_signup.password,
                'latitude': pending_signup.latitude,
                'longitude': pending_signup.longitude,
                'interests': pending_signup.interests,
                'pincode': pending_signup.pincode,
                'city': pending_signup.city,
                'state': pending_signup.state,
                'country': pending_signup.country,
                'device_id': device_id,
                'is_guest': False
            }
            
            serializer = UserProfileSerializer(data=user_data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            user = serializer.save()
        
        # Mark OTP as verified (only in production mode)
        if not debug:
            # Use filter + order_by to avoid MultipleObjectsReturned and pick the latest unverified OTP
            otp_to_mark = OTPVerification.objects.filter(identifier=identifier, is_verified=False).order_by('-created_at').first()
            if otp_to_mark:
                otp_to_mark.is_verified = True
                otp_to_mark.save()
        
        # Delete pending signup
        pending_signup.delete()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'User created successfully',
            'user_role': 'user',
            'user': {
                'userId': user.userId,
                'name': user.name,
                'email': user.email
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            },
            'location_details': {
                'pincode': user.pincode,
                'city': user.city,
                'state': user.state,
                'country': user.country
            }
        }, status=status.HTTP_200_OK)


class ResendOTPView(APIView):
    """
    POST /auth/resend-otp/
    Body: {"identifier": "email_or_phone"}

    Behavior:
    - Creates and stores a new OTP for the identifier and schedules delivery
    - Returns show_otp and message; does NOT return OTP in production
    """
    def post(self, request):
        device_id, app_mode, _, headers_valid, headers_error = get_headers(request)
        if not headers_valid:
            return Response({'error': headers_error}, status=status.HTTP_400_BAD_REQUEST)

        identifier = request.data.get('identifier')
        if not identifier:
            return Response({'error': 'Identifier is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Normalize and validate identifier (email or phone)
        is_email = '@' in identifier
        if is_email:
            identifier = identifier.strip().lower()
        else:
            is_valid, phone_result = validate_phone_number(identifier)
            if not is_valid:
                return Response({'error': phone_result}, status=status.HTTP_400_BAD_REQUEST)
            identifier = phone_result  # use cleaned numeric phone

        # Respect debug override if present
        debug_header = request.headers.get('debug', 'false').lower() == 'true'
        debug_body = request.data.get('debug', False)
        debug = debug_header or bool(debug_body)

        otp_result = handle_otp(identifier=identifier, is_email=is_email, app_mode=app_mode, debug=debug)

        if otp_result.get('session_token') or otp_result.get('otp'):
            # Store new OTP in DB (10-minute expiry for Sendmator)
            OTPVerification.objects.filter(identifier=identifier).delete()
            expires_at = timezone.now() + timedelta(minutes=10)
            otp_code = otp_result.get('otp') or "000000"  # Placeholder for Sendmator (6 chars max)
            session_token = otp_result.get('session_token')
            
            OTPVerification.objects.create(
                identifier=identifier, 
                otp_code=otp_code, 
                expires_at=expires_at,
                session_token=session_token
            )
            
            # Print OTP for debugging
            if otp_result.get('otp'):
                print(f"\n{'🔑 '*30}")
                print(f"RESEND OTP FOR {identifier}: {otp_result['otp']}")
                print(f"{'🔑 '*30}\n")

        sendmator_used = otp_result.get('sendmator_used', False)

        response = {
            'show_otp': otp_result.get('show_otp', True),
            'message': 'OTP resent via Sendmator' if sendmator_used else ('OTP resent' if not debug else 'Debug mode - no OTP sent'),
            'identifier': identifier,
            'sendmator': sendmator_used
        }

        # For staging or debug, include OTP for QA convenience
        if (app_mode == 'staging' or debug) and otp_result.get('otp'):
            response['otp'] = otp_result.get('otp')

        # If Sendmator or email failed, include OTP in response for testing/debugging
        if otp_result.get('error') and otp_result.get('otp'):
            response['otp'] = otp_result.get('otp')
            response['note'] = f"Fallback mode: {otp_result['error']}"

        return Response(response, status=status.HTTP_200_OK)


class DebugGetOTPView(APIView):
    """
    POST /auth/debug-get-otp/
    Body: {"identifier": "..."}
    Returns the latest OTP for identifier only if:
      - settings.DEBUG == True OR
      - Header 'x-debug-key' matches env DEBUG_API_KEY
    NOTE: This endpoint is for QA only and should NOT be enabled in production without secret.
    """
    def post(self, request):
        identifier = request.data.get('identifier')
        if not identifier:
            return Response({'error': 'Identifier is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Normalize and validate identifier (email or phone)
        is_email = '@' in identifier
        if is_email:
            identifier = identifier.strip().lower()
        else:
            is_valid, phone_result = validate_phone_number(identifier)
            if not is_valid:
                return Response({'error': phone_result}, status=status.HTTP_400_BAD_REQUEST)
            identifier = phone_result  # use cleaned numeric phone

        allowed = False
        if getattr(settings, 'DEBUG', False):
            allowed = True
        else:
            debug_key = request.headers.get('x-debug-key')
            if debug_key and debug_key == os.environ.get('DEBUG_API_KEY'):
                allowed = True

        if not allowed:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        otp_obj = OTPVerification.objects.filter(identifier=identifier).order_by('-created_at').first()
        if not otp_obj:
            return Response({'error': 'No OTP found for identifier'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'identifier': identifier, 'otp': otp_obj.otp_code}, status=status.HTTP_200_OK)


class InternalCheckSMTPView(APIView):
    """
    POST /internal/check-smtp/
    Protected endpoint to run a lightweight SMTP connectivity check.

    Requirements:
      - Header: x-admin-key must match env CHECK_SMTP_KEY
    Response (sanitized): {
      tcp_ok: bool,
      tcp_error: str|null,
      starttls_ok: bool,
      starttls_error: str|null,
      login_attempted: bool,
      login_ok: bool|null,
      login_error: str|null
    }
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        admin_key = os.environ.get('CHECK_SMTP_KEY')
        header_key = request.headers.get('x-admin-key')
        if not admin_key or header_key != admin_key:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        port = int(getattr(settings, 'EMAIL_PORT', 587))
        user = getattr(settings, 'EMAIL_HOST_USER', None)
        password = getattr(settings, 'EMAIL_HOST_PASSWORD', None)

        result = {
            'tcp_ok': False,
            'tcp_error': None,
            'starttls_ok': False,
            'starttls_error': None,
            'login_attempted': False,
            'login_ok': None,
            'login_error': None,
            'host': host,
            'port': port,
        }

        # TCP connect
        try:
            with socket.create_connection((host, port), timeout=10):
                result['tcp_ok'] = True
        except Exception as e:
            result['tcp_error'] = str(e)
            return Response(result, status=status.HTTP_200_OK)

        # STARTTLS handshake
        try:
            server = smtplib.SMTP(host=host, port=port, timeout=10)
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            result['starttls_ok'] = True
        except Exception as e:
            result['starttls_error'] = str(e)
            try:
                server.quit()
            except Exception:
                pass
            return Response(result, status=status.HTTP_200_OK)

        # Attempt login only if credentials present
        if user and password:
            result['login_attempted'] = True
            try:
                server.login(user, password)
                result['login_ok'] = True
            except smtplib.SMTPAuthenticationError as e:
                result['login_ok'] = False
                result['login_error'] = 'Authentication failed'
            except Exception as e:
                result['login_ok'] = False
                result['login_error'] = str(e)
        else:
            result['login_attempted'] = False

        try:
            server.quit()
        except Exception:
            pass

        return Response(result, status=status.HTTP_200_OK)
        


class SaveInterestsView(APIView):
    """
    POST /user/save-interests/
    Save/update user interests (replaces previous interests)
    
    Headers:
    - Authorization: Bearer <access_token>
    - Content-Type: application/json
    - is_debug: true | false (optional)
    
    Request: {"interests": ["tech", "sports", "entertainment"]}
    
    Validation:
    - interests is required and must be a non-empty array
    - Each interest ID must exist in the master interests table
    - Max limit: 10 interests
    - Duplicates are automatically removed
    - Previous interests are replaced (not appended)
    
    Requires authentication
    """
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return Response({'message': 'Authentication credentials were not provided'}, status=status.HTTP_401_UNAUTHORIZED)
        
        token = auth_header.replace('Bearer ', '').strip()
        
        # Decode and validate token
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
        except Exception:
            return Response({'message': 'Authentication credentials were not provided'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get user
        try:
            user = UserProfile.objects.get(userId=user_id)
        except UserProfile.DoesNotExist:
            return Response({'message': 'Authentication credentials were not provided'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get interests from request
        interests = request.data.get('interests')
        
        # Validation: interests is required
        if interests is None:
            return Response({'message': 'Invalid interests payload'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validation: must be an array
        if not isinstance(interests, list):
            return Response({'message': 'Invalid interests payload'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validation: must be non-empty
        if len(interests) == 0:
            return Response({'message': 'Invalid interests payload'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove duplicates while preserving order
        unique_interests = list(dict.fromkeys(interests))
        
        # Validation: max 10 interests
        if len(unique_interests) > 10:
            return Response({'message': 'Maximum 10 interests allowed'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate that all interest IDs exist in the master interests table
        valid_interests = []
        for interest_id in unique_interests:
            try:
                interest_obj = Interest.objects.get(interest_id=interest_id)
                valid_interests.append({
                    'id': interest_obj.interest_id,
                    'name': interest_obj.name
                })
            except Interest.DoesNotExist:
                return Response({'message': 'One or more interests are invalid'}, status=status.HTTP_404_NOT_FOUND)
        
        # Update user interests (replace, not append)
        user.interests = unique_interests
        user.save()
        
        return Response({
            'message': 'Interests updated successfully',
            'interests': valid_interests
        }, status=status.HTTP_200_OK)


class GetInterestsView(APIView):
    """
    POST /get-interests/
    Get available interests based on location
    Request: {"lat": "...", "long": "..."}
    Requires authentication (Bearer token for logged-in or guest users)
    """
    authentication_classes = []  # Disable DRF default authentication
    permission_classes = []  # Disable DRF default permissions
    
    def post(self, request):
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return Response({'error': 'No authentication token provided'}, status=status.HTTP_401_UNAUTHORIZED)
        
        token = auth_header.replace('Bearer ', '').strip()
        
        # Decode and validate token
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
        except Exception:
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Verify user exists (can be regular user or guest)
        try:
            user = UserProfile.objects.get(userId=user_id)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        lat = request.data.get('lat')
        long = request.data.get('long')
        
        if not lat or not long:
            return Response({'error': 'Location (lat, long) is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate coordinates
        coords_valid, coords_error, lat_float, long_float = validate_coordinates(lat, long)
        if not coords_valid:
            return Response({'error': coords_error}, status=status.HTTP_400_BAD_REQUEST)
        
        # Return all interests (location can be used for future filtering)
        interests = Interest.objects.all()
        serializer = InterestSerializer(interests, many=True)
        
        return Response({'interests': serializer.data}, status=status.HTTP_200_OK)


class GuestLoginView(APIView):
    """
    POST /login/guest/
    Create a guest user with interests and location
    Request: {"interests": [...], "lat": "...", "long": "..."}
    """
    def post(self, request):
        interests = request.data.get('interests', [])
        lat = request.data.get('lat')
        long = request.data.get('long')
        
        if not lat or not long:
            return Response({'error': 'Location (lat, long) is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate coordinates
        coords_valid, coords_error, lat_float, long_float = validate_coordinates(lat, long)
        if not coords_valid:
            return Response({'error': coords_error}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get location details
        location_details = get_location_details(lat, long)
        
        # Validate pincode from location details
        pincode_valid, pincode_error, cleaned_pincode = validate_pincode(location_details.get('pincode'))
        if not pincode_valid:
            return Response({'error': f"Invalid pincode from location: {pincode_error}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Use cleaned pincode if valid
        if cleaned_pincode:
            location_details['pincode'] = cleaned_pincode
        
        # Generate unique guest userId
        guest_id = f"guest_{uuid.uuid4().hex[:8]}"
        
        # Create guest user
        user_data = {
            'userId': guest_id,
            'interests': interests,
            'latitude': lat_float,
            'longitude': long_float,
            'pincode': location_details['pincode'],
            'city': location_details['city'],
            'state': location_details['state'],
            'country': location_details['country'],
            'is_guest': True
        }
        
        serializer = UserProfileSerializer(data=user_data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Guest user registered successfully',
                'user': {
                    'is_guest': True
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SetupProfileView(APIView):
    """
    POST /setup-profile/
    Update user profile with additional details
    
    Request: {
        "name": "...", 
        "bio": "...", 
        "gender": "...", 
        "age": 25, 
        "image_url": "...", 
        "additional_pincodes": [...], 
        "address_details": "...",
        "pincode": "...",
        "city": "...",
        "state": "...",
        "country": "..."
    }
    
    Returns complete profile with address information
    Requires authentication
    """
    authentication_classes = []  # Disable DRF default authentication
    permission_classes = []  # Disable DRF default permissions
    
    def post(self, request):
        try:
            # Get token from Authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            
            if not auth_header.startswith('Bearer '):
                return Response({'error': 'No authentication token provided'}, status=status.HTTP_401_UNAUTHORIZED)
            
            token = auth_header.replace('Bearer ', '').strip()
            
            # Decode and validate token
            try:
                access_token = AccessToken(token)
                user_id = access_token['user_id']
            except Exception as e:
                return Response({'error': f'Invalid or expired token: {str(e)}'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get user
            try:
                user = UserProfile.objects.get(userId=user_id)
            except UserProfile.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Update profile fields directly
            if 'name' in request.data:
                user.name = request.data['name']
            if 'bio' in request.data:
                user.bio = request.data['bio']
            if 'gender' in request.data:
                user.gender = request.data['gender']
            if 'age' in request.data:
                user.age = request.data['age']
            if 'image_url' in request.data:
                user.profilePhoto = request.data['image_url']
            if 'additional_pincodes' in request.data:
                user.additional_pincodes = request.data['additional_pincodes']
            if 'address_details' in request.data:
                user.address_details = request.data['address_details']
            
            # Update address/location fields if provided
            if 'pincode' in request.data:
                user.pincode = request.data['pincode']
            if 'city' in request.data:
                user.city = request.data['city']
            if 'state' in request.data:
                user.state = request.data['state']
            if 'country' in request.data:
                user.country = request.data['country']
            
            user.save()
            
            return Response({
                'message': 'Profile details saved successfully',
                'profile': {
                    'name': user.name,
                    'bio': user.bio,
                    'gender': user.gender,
                    'age': user.age,
                    'image_url': user.profilePhoto or '',
                    'address_details': user.address_details
                }
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AppInitView(APIView):
    """
    POST /app-init/
    Initialize app - auto-create guest user if no auth token
    
    Headers (Required):
    - x-device-id: Unique device identifier
    - x-app-mode: 'debug' or 'release'
    
    Headers (Optional):
    - Authorization: Bearer <token> (if user is logged in)
    
    Behavior:
    - If token provided: verify user exists, return user_role='user'
    - If no token but device_id: auto-create/find guest user, return user_role='guest'
    - Return user info and tokens
    """
    def post(self, request):
        # Get and validate headers
        device_id, app_mode, auth_token, headers_valid, headers_error = get_headers(request)
        if not headers_valid:
            return Response({'error': headers_error}, status=status.HTTP_400_BAD_REQUEST)
        
        # If user has auth token, verify user exists
        if auth_token:
            try:
                access_token = AccessToken(auth_token)
                user_id = access_token['user_id']
            except Exception:
                return Response({'error': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                user = UserProfile.objects.get(userId=user_id)
            except UserProfile.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Return authenticated user
            return Response({
                'message': 'App initialized',
                'user_role': 'user' if not user.is_guest else 'guest',
                'user': {
                    'userId': user.userId,
                    'name': user.name,
                    'email': user.email,
                    'is_guest': user.is_guest
                }
            }, status=status.HTTP_200_OK)
        
        # No token: auto-create or find guest user with device_id
        guest_user, created = get_or_create_guest_user(device_id)
        
        # Generate token for guest
        refresh = RefreshToken.for_user(guest_user)
        
        return Response({
            'message': 'Guest user ' + ('created' if created else 'found'),
            'user_role': 'guest',
            'user': {
                'userId': guest_user.userId,
                'is_guest': True
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class GetFeedView(APIView):
    """
    POST /get-feed/
    Get user feed based on location and interests
    Request: {"lat": "...", "long": "..."}
    Requires authentication
    """
    authentication_classes = []  # Disable DRF default authentication
    permission_classes = []  # Disable DRF default permissions

    def post(self, request):
        try:
            # Get token from Authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if not auth_header.startswith('Bearer '):
                return Response({'error': 'No authentication token provided'}, status=status.HTTP_401_UNAUTHORIZED)

            token = auth_header.replace('Bearer ', '').strip()

            # Decode and validate token
            from rest_framework_simplejwt.tokens import AccessToken
            try:
                access_token = AccessToken(token)
                user_id = access_token['user_id']
            except Exception as e:
                return Response({'error': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)

            # Get user
            try:
                user = UserProfile.objects.get(userId=user_id)
            except UserProfile.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            lat = request.data.get('lat')
            long = request.data.get('long')

            if not lat or not long:
                return Response({'error': 'Location (lat, long) is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate coordinates
            coords_valid, coords_error, lat_float, long_float = validate_coordinates(lat, long)
            if not coords_valid:
                return Response({'error': coords_error}, status=status.HTTP_400_BAD_REQUEST)

            # Get user's interests
            user_interests = user.interests if user.interests else []

            # Generate feed based on user's interests
            feed_data = self.generate_interest_based_feed(user_interests, lat_float, long_float, user.is_guest)

            return Response({
                'feed': feed_data,
                'user_interests': user_interests,
                'is_guest': user.is_guest,
                'location': {
                    'lat': str(lat_float),
                    'long': str(long_float),
                    'city': user.city,
                    'state': user.state
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def generate_interest_based_feed(self, user_interests, lat, long, is_guest):
        """
        Generate mock feed data based on user's interests
        In production, this would query actual posts/content from database
        """
        import random
        import uuid
        from datetime import datetime, timedelta

        feed_items = []

        # If no interests selected, return general feed
        if not user_interests:
            return [{
                'id': str(uuid.uuid4()),
                'type': 'general',
                'title': 'Welcome to Pinmate!',
                'content': 'Select your interests to get personalized content',
                'timestamp': datetime.now().isoformat(),
                'location': {'lat': lat, 'long': long}
            }]

        # Generate feed items for each interest
        for interest in user_interests[:5]:  # Limit to first 5 interests for demo
            # Create 2-3 posts per interest
            for i in range(random.randint(2, 3)):
                feed_item = {
                    'id': str(uuid.uuid4()),
                    'type': 'interest_post',
                    'interest': interest,
                    'title': f"{interest} Update #{i+1}",
                    'content': self.generate_content_for_interest(interest),
                    'image_url': f"https://picsum.photos/400/300?random={random.randint(1,1000)}",
                    'author': {
                        'name': f"User_{random.randint(1000,9999)}",
                        'is_guest': random.choice([True, False])
                    },
                    'timestamp': (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
                    'location': {
                        'lat': float(lat) + random.uniform(-0.01, 0.01),
                        'long': float(long) + random.uniform(-0.01, 0.01),
                        'distance': f"{random.uniform(0.5, 5.0):.1f} km away"
                    },
                    'engagement': {
                        'likes': random.randint(0, 50),
                        'comments': random.randint(0, 20),
                        'shares': random.randint(0, 10)
                    }
                }
                feed_items.append(feed_item)

        # Sort by timestamp (most recent first)
        feed_items.sort(key=lambda x: x['timestamp'], reverse=True)

        # Add a welcome message for guest users
        if is_guest and feed_items:
            welcome_item = {
                'id': str(uuid.uuid4()),
                'type': 'welcome',
                'title': '🎉 Welcome Guest!',
                'content': f'Enjoying content about {", ".join(user_interests[:3])}... Create an account to connect with others!',
                'timestamp': datetime.now().isoformat(),
                'location': {'lat': lat, 'long': long}
            }
            feed_items.insert(0, welcome_item)

        return feed_items[:20]  # Return max 20 items

    def generate_content_for_interest(self, interest):
        """
        Generate sample content based on interest category
        """
        content_templates = {
            'Art': [
                'Check out this amazing digital artwork I created! 🎨',
                'Art exhibition opening tonight - who\'s coming?',
                'Learning watercolor painting, here\'s my progress!',
                'Street art in the city is incredible!'
            ],
            'Travel': [
                'Just arrived in an amazing new city! ✈️',
                'Hidden gems you must visit in this location',
                'Travel tips for budget backpacking',
                'Sunset views from the mountain top!'
            ],
            'Food': [
                'Homemade pasta that turned out amazing! 🍝',
                'Street food adventure - trying local delicacies',
                'New restaurant review: must-try dishes!',
                'Cooking tutorial: easy 30-minute meals'
            ],
            'Technology': [
                'Latest gadget review - is it worth it? 📱',
                'Coding project I\'m working on',
                'Tech news: major breakthrough announced!',
                'Setting up my home automation system'
            ],
            'Fashion': [
                'Outfit of the day! What do you think? 👗',
                'Thrifting finds that I\'m loving',
                'Fashion tips for different body types',
                'Sustainable fashion brands to check out'
            ],
            'Fitness': [
                'Morning workout complete! 💪 Feeling energized',
                'New exercise routine that\'s working great',
                'Healthy meal prep for the week',
                'Running my first 10k - training updates!'
            ],
            'Photography': [
                'Captured this amazing sunset shot 📸',
                'Photography tips for beginners',
                'Editing workflow that I use',
                'Street photography collection'
            ],
            'Music': [
                'New song I\'m working on 🎵',
                'Concert review: best show ever!',
                'Music discovery: check out this artist',
                'Learning to play guitar - progress update'
            ],
            'Sports': [
                'Game day! Let\'s go team! ⚽',
                'Training session was intense today',
                'Sports analysis: breaking down the match',
                'Weekend hike completed - amazing views!'
            ],
            'DIY': [
                'DIY project completed! So proud of this 🛠️',
                'Upcycling old furniture into something new',
                'Home improvement tips and tricks',
                'Crafting tutorial: easy weekend projects'
            ]
        }

        import random
        templates = content_templates.get(interest, ['Sharing something interesting about ' + interest])
        return random.choice(templates)
