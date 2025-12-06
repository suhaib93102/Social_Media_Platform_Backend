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

