from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserProfileViewSet, FollowRequestViewSet, FollowerViewSet,
    PostViewSet, StoryViewSet, ChatViewSet,
    UserPostsView, UserStoriesView, ChatMessagesView
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'users', UserProfileViewSet, basename='user')
router.register(r'followRequests', FollowRequestViewSet, basename='followrequest')
router.register(r'followers', FollowerViewSet, basename='follower')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'stories', StoryViewSet, basename='story')
router.register(r'chats', ChatViewSet, basename='chat')

# URL patterns
urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Custom endpoints
    path('users/<str:userId>/posts/', UserPostsView.as_view(), name='user-posts'),
    path('users/<str:userId>/stories/', UserStoriesView.as_view(), name='user-stories'),
    path('chats/<int:chatId>/messages/', ChatMessagesView.as_view(), name='chat-messages'),
]
