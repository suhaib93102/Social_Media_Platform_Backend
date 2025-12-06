from rest_framework import serializers
from .models import UserProfile, FollowRequest, Follower, Post, Story, Chat, Message


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    
    class Meta:
        model = UserProfile
        fields = [
            'userId', 'name', 'gender', 'age', 'bio', 'email', 
            'profilePhoto', 'latitude', 'longitude', 'updatedAt',
            'activePincodes', 'followers', 'following', 'idCardUrl'
        ]
        read_only_fields = ['updatedAt']


class FollowRequestSerializer(serializers.ModelSerializer):
    """Serializer for FollowRequest model"""
    
    class Meta:
        model = FollowRequest
        fields = ['documentId', 'createdAt', 'fromUserId', 'toUserId', 'status']
        read_only_fields = ['documentId', 'createdAt']


class FollowerSerializer(serializers.ModelSerializer):
    """Serializer for Follower model"""
    
    class Meta:
        model = Follower
        fields = ['documentId', 'createdAt', 'followerId', 'followingId']
        read_only_fields = ['documentId', 'createdAt']


class PostLocationSerializer(serializers.Serializer):
    """Nested serializer for post location data"""
    accuracy = serializers.FloatField(required=False, allow_null=True)
    altitude = serializers.FloatField(required=False, allow_null=True)
    altitudeAccuracy = serializers.FloatField(required=False, allow_null=True)
    heading = serializers.FloatField(required=False, allow_null=True)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    speed = serializers.FloatField(required=False, allow_null=True)


class PostSerializer(serializers.ModelSerializer):
    """Serializer for Post model with nested location"""
    location = PostLocationSerializer(required=False)
    
    class Meta:
        model = Post
        fields = [
            'postId', 'description', 'mediaType', 'mediaURL', 
            'pincode', 'timestamp', 'userId', 'location'
        ]
        read_only_fields = ['postId', 'timestamp']
    
    def create(self, validated_data):
        location_data = validated_data.pop('location', {})
        post = Post.objects.create(location=location_data, **validated_data)
        return post
    
    def update(self, instance, validated_data):
        location_data = validated_data.pop('location', None)
        if location_data is not None:
            instance.location = location_data
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class StorySerializer(serializers.ModelSerializer):
    """Serializer for Story model"""
    
    class Meta:
        model = Story
        fields = [
            'storyId', 'createdAt', 'description', 'expireAt',
            'mediaType', 'mediaURL', 'userId'
        ]
        read_only_fields = ['storyId', 'createdAt']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model"""
    
    class Meta:
        model = Message
        fields = ['messageId', 'chatId', 'senderId', 'content', 'timestamp']
        read_only_fields = ['messageId', 'timestamp']


class ChatSerializer(serializers.ModelSerializer):
    """Serializer for Chat model"""
    
    class Meta:
        model = Chat
        fields = ['chatId', 'lastMessage', 'lastMessageTime', 'users']
        read_only_fields = ['chatId', 'lastMessageTime']


class ChatWithMessagesSerializer(serializers.ModelSerializer):
    """Serializer for Chat with messages"""
    messages = serializers.SerializerMethodField()
    
    class Meta:
        model = Chat
        fields = ['chatId', 'lastMessage', 'lastMessageTime', 'users', 'messages']
        read_only_fields = ['chatId', 'lastMessageTime']
    
    def get_messages(self, obj):
        messages = Message.objects.filter(chatId=obj.chatId)
        return MessageSerializer(messages, many=True).data
