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

            # Get user's interests
            user_interests = user.interests if user.interests else []

            # Generate feed based on user's interests
            feed_data = self.generate_interest_based_feed(user_interests, lat, long, user.is_guest)

            return Response({
                'feed': feed_data,
                'user_interests': user_interests,
                'is_guest': user.is_guest,
                'location': {
                    'lat': lat,
                    'long': long,
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
