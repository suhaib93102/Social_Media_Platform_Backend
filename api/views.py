from rest_framework.views import APIView, Response

# Health check endpoint
class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []
    def get(self, request):
        return Response({'status': 'ok'}, status=200)
from rest_framework.views import APIView, Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import requests
from .auth_views import get_location_details  # Import the function
class AddPincodeView(APIView):
    """
    POST /add-pincode
    Takes home-address and office-address with lat and long, returns location details for each.
    No authentication required.
    Request body: {"home-address": {"lat": ..., "long": ...}, "office-address": {"lat": ..., "long": ...}}
    Response: {"home-location": {...}, "office-location": {...}}
    """
    def post(self, request):
        home_address = request.data.get('home-address')
        office_address = request.data.get('office-address')
        
        response_data = {}
        
        if home_address:
            lat = home_address.get('lat')
            long = home_address.get('long')
            if lat is not None and long is not None:
                try:
                    lat_f = float(lat)
                    long_f = float(long)
                    location_details = get_location_details(lat_f, long_f)
                    response_data['home-location'] = location_details
                except (ValueError, TypeError):
                    response_data['home-location'] = {'error': 'Invalid lat/long for home'}
            else:
                response_data['home-location'] = {'error': 'lat and long required for home'}
        
        if office_address:
            lat = office_address.get('lat')
            long = office_address.get('long')
            if lat is not None and long is not None:
                try:
                    lat_f = float(lat)
                    long_f = float(long)
                    location_details = get_location_details(lat_f, long_f)
                    response_data['office-location'] = location_details
                except (ValueError, TypeError):
                    response_data['office-location'] = {'error': 'Invalid lat/long for office'}
            else:
                response_data['office-location'] = {'error': 'lat and long required for office'}
        
        return Response(response_data, status=200)

from rest_framework.views import APIView, Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import requests
from .auth_views import get_location_details  # Import the function
class SavePincodeView(APIView):
    """
    POST /save-pincode
    Requires JWT authentication. Saves home and office addresses with their locations.
    Request body: {"home-address": {"lat": ..., "long": ..., "address": ...}, "office-address": {"lat": ..., "long": ..., "address": ...}}
    """
    permission_classes = [IsAuthenticated]
    def post(self, request):
        home_address = request.data.get('home-address')
        office_address = request.data.get('office-address')
        
        user = request.user
        
        if home_address:
            lat = home_address.get('lat')
            long = home_address.get('long')
            pincode = home_address.get('pincode')
            address = home_address.get('address')
            if lat is not None and long is not None:
                try:
                    lat_f = float(lat)
                    long_f = float(long)
                    location_details = get_location_details(lat_f, long_f)
                    user.home_latitude = lat_f
                    user.home_longitude = long_f
                    user.home_pincode = pincode or location_details['pincode']
                    user.home_city = location_details['city']
                    user.home_state = location_details['state']
                    user.home_country = location_details['country']
                    if address:
                        user.personal_address = address
                except (ValueError, TypeError):
                    return Response({'error': 'Invalid lat/long for home'}, status=400)
        
        if office_address:
            lat = office_address.get('lat')
            long = office_address.get('long')
            pincode = office_address.get('pincode')
            address = office_address.get('address')
            if lat is not None and long is not None:
                try:
                    lat_f = float(lat)
                    long_f = float(long)
                    location_details = get_location_details(lat_f, long_f)
                    user.office_latitude = lat_f
                    user.office_longitude = long_f
                    user.office_pincode = pincode or location_details['pincode']
                    user.office_city = location_details['city']
                    user.office_state = location_details['state']
                    user.office_country = location_details['country']
                    if address:
                        user.work_address = address
                except (ValueError, TypeError):
                    return Response({'error': 'Invalid lat/long for office'}, status=400)
        
        try:
            user.save()
        except Exception as e:
            return Response({'error': f'Failed to save user: {str(e)}'}, status=500)
        
        response_data = {'message': 'Addresses saved successfully'}
        if home_address:
            response_data['home-location'] = {
                'pincode': user.home_pincode,
                'city': user.home_city,
                'state': user.home_state,
                'country': user.home_country,
                'address': user.personal_address
            }
        if office_address:
            response_data['office-location'] = {
                'pincode': user.office_pincode,
                'city': user.office_city,
                'state': user.office_state,
                'country': user.office_country,
                'address': user.work_address
            }
        return Response(response_data, status=200)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import UserProfile, FollowRequest, Follower, Post, Story, Chat, Message
from .serializers import (
    UserProfileSerializer, FollowRequestSerializer, FollowerSerializer,
    PostSerializer, StorySerializer, ChatSerializer, MessageSerializer,
    ChatWithMessagesSerializer
)
from .utils import create_follower_relationship


# ========== USER VIEWS ==========

class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserProfile
    GET /users/{userId} - Retrieve user profile
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = 'userId'
    
    @action(detail=True, methods=['get'], url_path='following')
    def following(self, request, userId=None):
        """GET /users/{userId}/following - Get list of users this user is following"""
        user = self.get_object()
        return Response({'following': user.following})
    
    @action(detail=True, methods=['get'], url_path='followers')
    def followers(self, request, userId=None):
        """GET /users/{userId}/followers - Get list of followers"""
        user = self.get_object()
        return Response({'followers': user.followers})
    
    @action(detail=True, methods=['post'], url_path='follow')
    def follow(self, request, userId=None):
        """POST /users/{userId}/follow - Send follow request"""
        from_user = self.get_object()
        to_user_id = request.data.get('toUserId')
        
        if not to_user_id:
            return Response({'error': 'toUserId is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if to_user exists
        try:
            to_user = UserProfile.objects.get(userId=to_user_id)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if request already exists
        existing_request = FollowRequest.objects.filter(
            fromUserId=userId, toUserId=to_user_id
        ).first()
        
        if existing_request:
            return Response({'message': 'Follow request already sent', 'status': existing_request.status})
        
        # Create follow request
        follow_request = FollowRequest.objects.create(
            fromUserId=userId,
            toUserId=to_user_id,
            status='pending'
        )
        
        serializer = FollowRequestSerializer(follow_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='accept-follow')
    def accept_follow(self, request, userId=None):
        """POST /users/{userId}/accept-follow - Accept follow request"""
        to_user = self.get_object()
        from_user_id = request.data.get('fromUserId')
        new_status = request.data.get('status', 'accepted')
        
        if not from_user_id:
            return Response({'error': 'fromUserId is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Find the follow request
        follow_request = FollowRequest.objects.filter(
            fromUserId=from_user_id, toUserId=userId
        ).first()
        
        if not follow_request:
            return Response({'error': 'Follow request not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Update status
        follow_request.status = new_status
        follow_request.save()
        
        # If accepted, create follower relationship
        if new_status == 'accepted':
            create_follower_relationship(from_user_id, userId)
        
        serializer = FollowRequestSerializer(follow_request)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='unfollow')
    def unfollow(self, request, userId=None):
        """POST /users/{userId}/unfollow - Unfollow a user"""
        from_user = self.get_object()
        to_user_id = request.data.get('toUserId')
        
        if not to_user_id:
            return Response({'error': 'toUserId is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Delete follower relationship
        follower = Follower.objects.filter(
            followerId=userId, followingId=to_user_id
        ).first()
        
        if follower:
            follower.delete()
            
            # Update user arrays
            from_user.following = [u for u in from_user.following if u != to_user_id]
            from_user.save()
            
            try:
                to_user = UserProfile.objects.get(userId=to_user_id)
                to_user.followers = [u for u in to_user.followers if u != userId]
                to_user.save()
            except UserProfile.DoesNotExist:
                pass
            
            return Response({'message': 'Unfollowed successfully'})
        
        return Response({'error': 'Not following this user'}, status=status.HTTP_404_NOT_FOUND)


# ========== FOLLOW REQUEST VIEWS ==========

class FollowRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for FollowRequest
    GET /followRequests/{documentId}
    POST /followRequests
    PATCH /followRequests/{documentId}
    """
    queryset = FollowRequest.objects.all()
    serializer_class = FollowRequestSerializer
    lookup_field = 'documentId'
    
    def partial_update(self, request, *args, **kwargs):
        """Handle PATCH request to update follow request status"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # If status is being changed to 'accepted', create follower relationship
        if 'status' in request.data and request.data['status'] == 'accepted':
            create_follower_relationship(instance.fromUserId, instance.toUserId)
        
        self.perform_update(serializer)
        return Response(serializer.data)


# ========== FOLLOWER VIEWS ==========

class FollowerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Follower
    GET /followers/{documentId}
    """
    queryset = Follower.objects.all()
    serializer_class = FollowerSerializer
    lookup_field = 'documentId'


# ========== POST VIEWS ==========

class PostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Post
    GET /posts/{postId}
    POST /posts
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_field = 'postId'
    
    def get_permissions(self):
        """Require authentication for creating posts"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return []
    
    def perform_create(self, serializer):
        """Set the userId from the authenticated user when creating a post"""
        serializer.save(userId=self.request.user.userId)


class UserPostsView(APIView):
    """
    GET /users/{userId}/posts - Get all posts by a user
    """
    def get(self, request, userId):
        posts = Post.objects.filter(userId=userId)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)


# ========== STORY VIEWS ==========

class StoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Story
    GET /stories/{storyId}
    POST /stories
    """
    queryset = Story.objects.all()
    serializer_class = StorySerializer
    lookup_field = 'storyId'


class UserStoriesView(APIView):
    """
    GET /users/{userId}/stories - Get all active (not expired) stories for user
    """
    def get(self, request, userId):
        now = timezone.now()
        stories = Story.objects.filter(userId=userId, expireAt__gt=now)
        serializer = StorySerializer(stories, many=True)
        return Response(serializer.data)


# ========== CHAT VIEWS ==========

class ChatViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Chat
    GET /chats/{chatId}
    POST /chats
    """
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    lookup_field = 'chatId'
    
    @action(detail=False, methods=['post'], url_path='get-or-create')
    def get_or_create(self, request):
        """POST /chats/get-or-create/ - Get or create chat between two users"""
        user1 = request.data.get('user1')
        user2 = request.data.get('user2')
        
        if not user1 or not user2:
            return Response({'error': 'Both user1 and user2 are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Normalize user order (smaller userId first)
        users = sorted([user1, user2])
        
        # Find existing chat
        existing_chat = Chat.objects.filter(users__contains=users).first()
        
        if existing_chat:
            serializer = ChatSerializer(existing_chat)
            return Response(serializer.data)
        
        # Create new chat
        new_chat = Chat.objects.create(users=users)
        serializer = ChatSerializer(new_chat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChatMessagesView(APIView):
    """
    GET /chats/{chatId}/messages - Get messages for a chat
    POST /chats/{chatId}/messages - Send a message
    """
    
    def get(self, request, chatId):
        """Get all messages for a chat"""
        messages = Message.objects.filter(chatId=chatId)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    def post(self, request, chatId):
        """Send a message and update chat's lastMessage and lastMessageTime"""
        # Verify chat exists
        chat = get_object_or_404(Chat, chatId=chatId)
        
        # Create message
        data = request.data.copy()
        data['chatId'] = chatId
        serializer = MessageSerializer(data=data)
        
        if serializer.is_valid():
            message = serializer.save()
            
            # Update chat's lastMessage and lastMessageTime
            chat.lastMessage = message.content
            chat.lastMessageTime = message.timestamp
            chat.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

