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
import uuid
import requests
import random
import re
from datetime import timedelta
from django.utils import timezone


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


def send_otp_email(email, otp_code):
    """
    Send OTP via email
    For production, integrate with email service (SendGrid, AWS SES, etc.)
    """
    try:
        # TODO: Implement actual email sending
        # For now, just print to console (development mode)
        print(f"[OTP EMAIL] Sending OTP {otp_code} to {email}")
        print(f"Email would be sent with subject: 'Your Pinmate Verification Code'")
        print(f"Body: 'Your verification code is: {otp_code}. Valid for 10 minutes.'")
        return True
    except Exception as e:
        print(f"Error sending email OTP: {e}")
        return False


def send_otp_sms(phone_number, otp_code):
    """
    Send OTP via SMS
    For production, integrate with SMS service (Twilio, AWS SNS, etc.)
    """
    try:
        # TODO: Implement actual SMS sending
        # For now, just print to console (development mode)
        print(f"[OTP SMS] Sending OTP {otp_code} to {phone_number}")
        print(f"SMS would be sent: 'Your Pinmate verification code is: {otp_code}. Valid for 10 minutes.'")
        return True
    except Exception as e:
        print(f"Error sending SMS OTP: {e}")
        return False


def create_otp_record(identifier, otp_code):
    """Create OTP verification record"""
    expires_at = timezone.now() + timedelta(minutes=10)
    OTPVerification.objects.create(
        identifier=identifier,
        otp_code=otp_code,
        expires_at=expires_at
    )


def get_location_details(lat, long):
    """
    Get location details (pincode, city, state, country) from coordinates.
    Uses a geocoding API (Nominatim OpenStreetMap)
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
        
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={long}&format=json"
        headers = {'User-Agent': 'PinmateApp/1.0'}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if geocoding was successful
            if 'error' in data:
                print(f"Geocoding API error: {data['error']}")
                return {
                    'pincode': '000000',
                    'city': 'Location Not Found',
                    'state': 'Location Not Found',
                    'country': 'Location Not Found'
                }
            
            address = data.get('address', {})
            
            return {
                'pincode': address.get('postcode', '000000'),
                'city': address.get('city') or address.get('town') or address.get('village', 'Unknown'),
                'state': address.get('state', 'Unknown'),
                'country': address.get('country', 'Unknown')
            }
        else:
            print(f"Geocoding API returned status {response.status_code}")
            
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
        debug_param = request.data.get('debug', False)  # New debug parameter
        
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
        
        # Generate userId from email or phone
        if email_id:
            user_id = email_id.split('@')[0]
            identifier = email_id
        else:
            user_id = f"user_{number}"
            identifier = number
        
        # Check if user already exists
        if UserProfile.objects.filter(userId=user_id).exists():
            return Response({'error': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        # Determine bypass according to exact table rules:
        # - If header x-app-mode is 'release' AND request body debug==True => SKIP OTP (bypass)
        # - Otherwise, OTP is required (even if request debug==True when x-app-mode=='debug')
        bypass_debug_parameter = True if (app_mode == 'release' and bool(debug_param)) else False
        
        if bypass_debug_parameter:
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
                    'show_otp': False,
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
                    },
                    'location_details': location_details
                }, status=status.HTTP_200_OK)
            else:
                # Create new user
                user_data = {
                    'userId': user_id,
                    'email': email_id,
                    'phone_number': number,
                    'password': hashed_password,
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
                        'show_otp': False,
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
                        },
                        'location_details': location_details
                    }, status=status.HTTP_201_CREATED)
                
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Production mode or OTP required: Generate and send OTP
        otp_code = generate_otp()
        
        # Delete old OTP codes for this identifier
        OTPVerification.objects.filter(identifier=identifier).delete()
        
        # Create new OTP record
        create_otp_record(identifier, otp_code)
        
        # Send OTP via email or SMS
        if email_id:
            send_otp_email(email_id, otp_code)
        else:
            send_otp_sms(number, otp_code)
        
        return Response({
            'show_otp': True,
            'message': get_otp_message(app_mode),
            'identifier': identifier
        }, status=status.HTTP_200_OK)


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
        debug_param = request.data.get('debug', False)
        
        if not identifier:
            return Response({'error': 'Identifier is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Determine bypass according to exact table rules:
        # bypass when header x-app-mode is 'release' AND request debug==True
        bypass_debug_parameter = True if (app_mode == 'release' and bool(debug_param)) else False
        
        if bypass_debug_parameter:
            # Skip OTP verification entirely and continue
            pass
        else:
            # Not bypassing - perform OTP verification
            # Check environment debug mode (NODE_ENV=development + x-app-mode=debug)
            debug_env = is_debug_mode(app_mode)
            if debug_env:
                # Debug env: require entered_otp and accept fixed 123456
                if not entered_otp:
                    return Response({'error': 'Identifier and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)
                if str(entered_otp) != '123456':
                    return Response({'error': 'Invalid OTP (use 123456 in debug mode)'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Production mode: require entered_otp and verify actual OTP
                if not entered_otp:
                    return Response({'error': 'Identifier and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    otp_record = OTPVerification.objects.filter(
                        identifier=identifier,
                        is_verified=False
                    ).latest('created_at')
                except OTPVerification.DoesNotExist:
                    return Response({'error': 'No OTP found. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
                
                # Check if OTP is expired
                if otp_record.is_expired():
                    return Response({'error': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
                
                # Verify OTP
                if otp_record.otp_code != str(entered_otp):
                    return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
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
            try:
                otp_record = OTPVerification.objects.get(identifier=identifier)
                otp_record.is_verified = True
                otp_record.save()
            except OTPVerification.DoesNotExist:
                pass
        
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
        
        serializer = UserProfileSerializer(data=user_data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Mark OTP as verified
            otp_record.is_verified = True
            otp_record.save()
            
            # Delete pending signup
            pending_signup.delete()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'User created successfully',
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
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
                    'address_details': user.address_details,
                    'address': {
                        'pincode': user.pincode or '',
                        'city': user.city or '',
                        'state': user.state or '',
                        'country': user.country or ''
                    }
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
