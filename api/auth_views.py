from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile
from .serializers import UserProfileSerializer


class SignupView(APIView):
    """
    POST /auth/signup/
    Create a new user account with password
    """
    def post(self, request):
        # Validate that password is provided
        if 'password' not in request.data:
            return Response(
                {'error': 'Password is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = UserProfileSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens (use for_user to set standard claims)
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
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST /auth/login/
    Login with userId/email and password, returns JWT tokens
    """
    def post(self, request):
        identifier = request.data.get('userId') or request.data.get('email')
        password = request.data.get('password')
        
        if not identifier or not password:
            return Response(
                {'error': 'userId/email and password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to find user by userId or email
        try:
            if '@' in identifier:
                user = UserProfile.objects.get(email=identifier)
            else:
                user = UserProfile.objects.get(userId=identifier)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Invalid credentials'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify password
        if not check_password(password, user.password):
            return Response(
                {'error': 'Invalid credentials'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate JWT tokens (use for_user to set standard claims)
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
