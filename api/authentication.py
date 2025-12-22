from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser
from .models import UserProfile

class UserProfileJWTAuthentication(JWTAuthentication):
    """Custom JWT authentication that maps token to UserProfile instead of default Django User model"""

    user_id_claim = 'user_id'  # Set the claim name

    def get_user(self, validated_token):
        """Return a UserProfile object based on token claims.
        Will attempt to read the `user_id` claim. For our custom tokens, this should
        match `UserProfile.userId`.
        """
        user_id = validated_token.get(self.user_id_claim)
        # Fallback to common names
        if not user_id:
            user_id = validated_token.get('userId') or validated_token.get('email')

        if not user_id:
            return AnonymousUser()

        try:
            return UserProfile.objects.get(userId=user_id)
        except UserProfile.DoesNotExist:
            return AnonymousUser()
