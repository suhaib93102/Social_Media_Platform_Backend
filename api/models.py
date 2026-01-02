from django.db import models
from django.conf import settings
from django.utils import timezone
import json

# Conditional import for PostgreSQL ArrayField
try:
    from django.contrib.postgres.fields import ArrayField
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False


def get_array_field(*args, **kwargs):
    """
    Returns ArrayField for PostgreSQL or JSONField for other databases
    """
    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
        return ArrayField(*args, **kwargs)
    else:
        # Use JSONField for SQLite/other databases
        return models.JSONField(default=list, **{k: v for k, v in kwargs.items() if k not in ['base_field', 'size']})


class UserProfile(models.Model):
    """User profile model matching the users collection"""
    userId = models.CharField(max_length=255, primary_key=True, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=50, blank=True, null=True)
    age = models.IntegerField(null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)  # Hashed password
    profilePhoto = models.URLField(blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    updatedAt = models.DateTimeField(auto_now=True)
    
    # Device tracking for guest auto-entry
    device_id = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
    
    # Location details
    pincode = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # Interests and pincodes
    interests = models.JSONField(default=list, blank=True)
    activePincodes = models.JSONField(default=list, blank=True)
    additional_pincodes = models.JSONField(default=list, blank=True)
    
    # Social
    followers = models.JSONField(default=list, blank=True)
    following = models.JSONField(default=list, blank=True)
    
    # Guest user flag
    is_guest = models.BooleanField(default=False)
    
    # Address
    address_details = models.TextField(blank=True, null=True)
    personal_address = models.TextField(blank=True, null=True)
    work_address = models.TextField(blank=True, null=True)
    
    # Home location details
    home_latitude = models.FloatField(null=True, blank=True)
    home_longitude = models.FloatField(null=True, blank=True)
    home_pincode = models.CharField(max_length=20, blank=True, null=True)
    home_city = models.CharField(max_length=100, blank=True, null=True)
    home_state = models.CharField(max_length=100, blank=True, null=True)
    home_country = models.CharField(max_length=100, blank=True, null=True)
    
    # Office location details
    office_latitude = models.FloatField(null=True, blank=True)
    office_longitude = models.FloatField(null=True, blank=True)
    office_pincode = models.CharField(max_length=20, blank=True, null=True)
    office_city = models.CharField(max_length=100, blank=True, null=True)
    office_state = models.CharField(max_length=100, blank=True, null=True)
    office_country = models.CharField(max_length=100, blank=True, null=True)
    
    idCardUrl = models.URLField(blank=True, null=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.name} ({self.userId})" if self.name else f"User {self.userId}"
    
    USERNAME_FIELD = 'userId'
    REQUIRED_FIELDS = []

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_username(self):
        return self.userId


class OTPVerification(models.Model):
    """Store OTP codes for email/phone verification"""
    identifier = models.CharField(max_length=255, db_index=True)  # email or phone
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    session_token = models.TextField(null=True, blank=True)  # Sendmator session token
    
    class Meta:
        db_table = 'otp_verifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.identifier}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at


class PendingSignup(models.Model):
    """Store signup data until OTP is verified"""
    identifier = models.CharField(max_length=255, unique=True, db_index=True)  # email or phone
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    password = models.CharField(max_length=255)  # Hashed password
    latitude = models.FloatField()
    longitude = models.FloatField()
    interests = models.JSONField(default=list)
    pincode = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    device_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'pending_signups'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Pending signup for {self.identifier}"


class Interest(models.Model):
    """Interest model for user interests selection"""
    interest_id = models.SlugField(max_length=100, primary_key=True, unique=True)
    name = models.CharField(max_length=100)
    image = models.URLField(blank=True, null=True)
    
    class Meta:
        db_table = 'interests'
    
    def __str__(self):
        return self.name


class FollowRequest(models.Model):
    """Follow request model"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    documentId = models.AutoField(primary_key=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    fromUserId = models.CharField(max_length=255)
    toUserId = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        db_table = 'followRequests'
        unique_together = ['fromUserId', 'toUserId']

    def __str__(self):
        return f"{self.fromUserId} -> {self.toUserId} ({self.status})"


class Follower(models.Model):
    """Follower relationship model"""
    documentId = models.AutoField(primary_key=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    followerId = models.CharField(max_length=255)
    followingId = models.CharField(max_length=255)

    class Meta:
        db_table = 'followers'
        unique_together = ['followerId', 'followingId']

    def __str__(self):
        return f"{self.followerId} follows {self.followingId}"


class Post(models.Model):
    """Post model with location data"""
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    postId = models.AutoField(primary_key=True)
    description = models.TextField(blank=True, null=True)
    mediaType = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES)
    mediaURL = models.URLField()
    pincode = models.CharField(max_length=10, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    userId = models.CharField(max_length=255)
    
    # Location fields stored as JSON
    location = models.JSONField(default=dict)  # Contains: accuracy, altitude, altitudeAccuracy, heading, latitude, longitude, speed

    class Meta:
        db_table = 'posts'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Post {self.postId} by {self.userId}"


class Story(models.Model):
    """Story model with expiration"""
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    storyId = models.AutoField(primary_key=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    expireAt = models.DateTimeField()
    mediaType = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES)
    mediaURL = models.URLField()
    userId = models.CharField(max_length=255)

    class Meta:
        db_table = 'stories'
        ordering = ['-createdAt']

    def __str__(self):
        return f"Story {self.storyId} by {self.userId}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expireAt


class Chat(models.Model):
    """Chat model for conversations"""
    chatId = models.AutoField(primary_key=True)
    lastMessage = models.TextField(blank=True, null=True)
    lastMessageTime = models.DateTimeField(null=True, blank=True)
    users = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'chats'
        ordering = ['-lastMessageTime']

    def __str__(self):
        return f"Chat {self.chatId} - {', '.join(self.users) if isinstance(self.users, list) else self.users}"


class Message(models.Model):
    """Message model for chat messages"""
    messageId = models.AutoField(primary_key=True)
    chatId = models.IntegerField()
    senderId = models.CharField(max_length=255)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['timestamp']

    def __str__(self):
        return f"Message {self.messageId} in Chat {self.chatId}"


class PostLike(models.Model):
    """Model for post likes"""
    likeId = models.AutoField(primary_key=True)
    postId = models.IntegerField(db_index=True)
    userId = models.CharField(max_length=255, db_index=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'post_likes'
        unique_together = ['postId', 'userId']
        ordering = ['-createdAt']

    def __str__(self):
        return f"{self.userId} liked Post {self.postId}"


class PostSave(models.Model):
    """Model for saved/bookmarked posts"""
    saveId = models.AutoField(primary_key=True)
    postId = models.IntegerField(db_index=True)
    userId = models.CharField(max_length=255, db_index=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'post_saves'
        unique_together = ['postId', 'userId']
        ordering = ['-createdAt']

    def __str__(self):
        return f"{self.userId} saved Post {self.postId}"


class PostComment(models.Model):
    """Model for post comments"""
    commentId = models.AutoField(primary_key=True)
    postId = models.IntegerField(db_index=True)
    userId = models.CharField(max_length=255, db_index=True)
    content = models.TextField()
    createdAt = models.DateTimeField(auto_now_add=True)
    parentCommentId = models.IntegerField(null=True, blank=True)  # For nested comments

    class Meta:
        db_table = 'post_comments'
        ordering = ['-createdAt']

    def __str__(self):
        return f"Comment {self.commentId} on Post {self.postId}"


class BlockedUser(models.Model):
    """Model for blocked users"""
    blockId = models.AutoField(primary_key=True)
    blockerUserId = models.CharField(max_length=255, db_index=True)
    blockedUserId = models.CharField(max_length=255, db_index=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blocked_users'
        unique_together = ['blockerUserId', 'blockedUserId']
        ordering = ['-createdAt']

    def __str__(self):
        return f"{self.blockerUserId} blocked {self.blockedUserId}"


class ReportedContent(models.Model):
    """Model for reported posts/users"""
    CONTENT_TYPE_CHOICES = [
        ('post', 'Post'),
        ('user', 'User'),
        ('comment', 'Comment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('action_taken', 'Action Taken'),
        ('dismissed', 'Dismissed'),
    ]
    
    reportId = models.AutoField(primary_key=True)
    reporterUserId = models.CharField(max_length=255, db_index=True)
    contentType = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    contentId = models.IntegerField(db_index=True)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reported_content'
        ordering = ['-createdAt']

    def __str__(self):
        return f"Report {self.reportId} - {self.contentType} {self.contentId}"

