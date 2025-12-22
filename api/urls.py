from .views import HealthCheckView
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserProfileViewSet, FollowRequestViewSet, FollowerViewSet,
    PostViewSet, StoryViewSet, ChatViewSet,
    UserPostsView, UserStoriesView, ChatMessagesView,
    AddPincodeView, SavePincodeView
)
from .auth_views import (
    SignupView, LoginView, GetInterestsView, 
    GuestLoginView, SetupProfileView, GetFeedView,
    VerifyOTPView, SaveInterestsView, AppInitView, ResendOTPView, DebugGetOTPView
)
from .auth_views import InternalCheckSMTPView

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
    # Health check endpoint
    path('health/', HealthCheckView.as_view(), name='health'),
    # App initialization
    path('app-init/', AppInitView.as_view(), name='app-init'),

    # Pincode endpoints
    path('add-pincode/', AddPincodeView.as_view(), name='add-pincode'),
    path('save-pincode/', SavePincodeView.as_view(), name='save-pincode'),
    
    # Authentication endpoints
    path('auth/signup/', SignupView.as_view(), name='auth-signup'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('auth/debug-get-otp/', DebugGetOTPView.as_view(), name='debug-get-otp'),
    path('internal/check-smtp/', InternalCheckSMTPView.as_view(), name='internal-check-smtp'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Onboarding endpoints
    path('get-interests/', GetInterestsView.as_view(), name='get-interests'),
    path('user/save-interests/', SaveInterestsView.as_view(), name='save-interests'),
    path('login/guest/', GuestLoginView.as_view(), name='guest-login'),
    path('setup-profile/', SetupProfileView.as_view(), name='setup-profile'),
    path('get-feed/', GetFeedView.as_view(), name='get-feed'),
    
    # Router URLs
    path('', include(router.urls)),
    
    # Custom endpoints
    path('users/<str:userId>/posts/', UserPostsView.as_view(), name='user-posts'),
    path('users/<str:userId>/stories/', UserStoriesView.as_view(), name='user-stories'),
    path('chats/<int:chatId>/messages/', ChatMessagesView.as_view(), name='chat-messages'),
]
