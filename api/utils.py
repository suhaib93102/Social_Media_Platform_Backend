"""
Utility functions for the API
"""
from .models import Follower, UserProfile


def create_follower_relationship(from_user_id, to_user_id):
    """
    Create a follower relationship when a follow request is accepted.
    Also updates the followers and following arrays in UserProfile.
    """
    # Create the follower entry
    follower, created = Follower.objects.get_or_create(
        followerId=from_user_id,
        followingId=to_user_id
    )
    
    # Update UserProfile followers and following arrays
    try:
        # Add to_user_id to from_user's following list
        from_user = UserProfile.objects.get(userId=from_user_id)
        if to_user_id not in from_user.following:
            from_user.following.append(to_user_id)
            from_user.save()
    except UserProfile.DoesNotExist:
        pass
    
    try:
        # Add from_user_id to to_user's followers list
        to_user = UserProfile.objects.get(userId=to_user_id)
        if from_user_id not in to_user.followers:
            to_user.followers.append(from_user_id)
            to_user.save()
    except UserProfile.DoesNotExist:
        pass
    
    return follower


def remove_follower_relationship(from_user_id, to_user_id):
    """
    Remove a follower relationship.
    Also updates the followers and following arrays in UserProfile.
    """
    # Delete the follower entry
    Follower.objects.filter(
        followerId=from_user_id,
        followingId=to_user_id
    ).delete()
    
    # Update UserProfile followers and following arrays
    try:
        # Remove to_user_id from from_user's following list
        from_user = UserProfile.objects.get(userId=from_user_id)
        if to_user_id in from_user.following:
            from_user.following.remove(to_user_id)
            from_user.save()
    except UserProfile.DoesNotExist:
        pass
    
    try:
        # Remove from_user_id from to_user's followers list
        to_user = UserProfile.objects.get(userId=to_user_id)
        if from_user_id in to_user.followers:
            to_user.followers.remove(from_user_id)
            to_user.save()
    except UserProfile.DoesNotExist:
        pass
