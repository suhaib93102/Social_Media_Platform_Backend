from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from .models import UserProfile, Interest
from .serializers import UserProfileSerializer, InterestSerializer
import uuid
import requests


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
    Request: {"email_id": "...", "password": "...", "lat": "...", "long": "...", "interests": [...]}
    or {"number": "...", "password": "...", "lat": "...", "long": "...", "interests": [...]}
    """
    def post(self, request):
        email_id = request.data.get('email_id')
        number = request.data.get('number')
        password = request.data.get('password')
        lat = request.data.get('lat')
        long = request.data.get('long')
        interests = request.data.get('interests', [])
        
        # Validate input
        if not password:
            return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not email_id and not number:
            return Response({'error': 'Either email_id or number is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not lat or not long:
            return Response({'error': 'Location (lat, long) is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get location details from coordinates
        location_details = get_location_details(lat, long)
        
        # Generate userId from email or phone
        if email_id:
            user_id = email_id.split('@')[0]
        else:
            user_id = f"user_{number}"
        
        # Check if user already exists
        if UserProfile.objects.filter(userId=user_id).exists():
            return Response({'error': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        if email_id and UserProfile.objects.filter(email=email_id).exists():
            return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)
        
        if number and UserProfile.objects.filter(phone_number=number).exists():
            return Response({'error': 'Phone number already registered'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user data
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
            'is_guest': False
        }
        
        serializer = UserProfileSerializer(data=user_data)
        if serializer.is_valid():
            user = serializer.save()
            
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
                'location_details': location_details
            }, status=status.HTTP_201_CREATED)
        
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


class GetInterestsView(APIView):
    """
    POST /get-interests/
    Get available interests based on location
    Request: {"lat": "...", "long": "..."}
    """
    def post(self, request):
        lat = request.data.get('lat')
        long = request.data.get('long')
        
        if not lat or not long:
            return Response({'error': 'Location (lat, long) is required'}, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        # Get location details
        location_details = get_location_details(lat, long)
        
        # Generate unique guest userId
        guest_id = f"guest_{uuid.uuid4().hex[:8]}"
        
        # Create guest user
        user_data = {
            'userId': guest_id,
            'interests': interests,
            'latitude': float(lat),
            'longitude': float(long),
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
    Request: {"name": "...", "bio": "...", "gender": "...", "age": 25, "image_url": "...", "additional_pincodes": [...]}
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
            
            user.save()
            return Response({'message': 'Profile Details saved successfully.'}, status=status.HTTP_200_OK)
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetFeedView(APIView):
    """
    POST /get-feed/
    Get user feed based on location
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
            
            # Placeholder response - implement feed logic based on requirements
            return Response({
                'feed': [],
                'message': 'Feed endpoint - to be implemented with business logic'
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
