from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from .models import (
    UserProfile, Post, PostLike, PostSave, PostComment, 
    BlockedUser, ReportedContent, Follower
)
import math


class HomeFeedView(APIView):
    """
    POST /home-feed
    
    Deliver personalized, paginated home feed with structured snippets
    
    Headers:
    - Authorization: Bearer <access_token> (Required)
    - Content-Type: application/json
    
    Request Body:
    {
        "page_id": 0,
        "limit": 10
    }
    
    Response:
    {
        "results": [
            {
                "type": "POST_CARD_SNIPPET_TYPE_1",
                "post_card_snippet_type_1": { ... }
            }
        ],
        "has_more": true
    }
    """
    
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        # Step 1: Authentication Validation
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return Response({
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication credentials were not provided'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token = auth_header.replace('Bearer ', '').strip()
        
        # Decode and validate token
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
        except Exception:
            return Response({
                'error': {
                    'code': 'INVALID_TOKEN',
                    'message': 'Invalid or expired authentication token'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get user and verify account status
        try:
            current_user = UserProfile.objects.get(userId=user_id)
        except UserProfile.DoesNotExist:
            return Response({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User account not found'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is guest (guests shouldn't access feed)
        if current_user.is_guest:
            return Response({
                'error': {
                    'code': 'ACCESS_DENIED',
                    'message': 'Guest users cannot access home feed'
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Step 2: Request Validation
        page_id = request.data.get('page_id')
        limit = request.data.get('limit', 10)
        
        # Validate page_id
        if page_id is None:
            return Response({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'page_id is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            page_id = int(page_id)
            if page_id < 0:
                raise ValueError()
        except (ValueError, TypeError):
            return Response({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'page_id must be a non-negative integer'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate and cap limit
        try:
            limit = int(limit)
            if limit < 1:
                limit = 10
            elif limit > 20:
                limit = 20
        except (ValueError, TypeError):
            limit = 10
        
        # Step 3: User Context Resolution
        print("DEBUG: Starting user context resolution")
        # Get blocked users
        blocked_user_ids = set(
            BlockedUser.objects.filter(blockerUserId=user_id).values_list('blockedUserId', flat=True)
        )
        
        # Get users who blocked current user
        blocked_by_user_ids = set(
            BlockedUser.objects.filter(blockedUserId=user_id).values_list('blockerUserId', flat=True)
        )
        
        # Combine both blocked lists
        excluded_user_ids = blocked_user_ids.union(blocked_by_user_ids)
        
        # Get following list
        following_ids = set(
            Follower.objects.filter(followerId=user_id).values_list('followingId', flat=True)
        )
        
        # Get reported posts by this user
        reported_post_ids = set(
            ReportedContent.objects.filter(
                reporterUserId=user_id,
                contentType='post'
            ).values_list('contentId', flat=True)
        )
        
        # Get user's interests and location for personalization
        user_interests = current_user.interests or []
        user_pincode = current_user.pincode
        
        # Step 4: Feed Candidate Collection
        # Build base query
        feed_query = Post.objects.exclude(userId__in=excluded_user_ids)
        
        # Exclude reported posts
        if reported_post_ids:
            feed_query = feed_query.exclude(postId__in=reported_post_ids)
        
        # Get posts first
        feed_posts = list(feed_query.order_by('-timestamp'))
        
        # Get engagement counts in bulk
        post_ids = [post.postId for post in feed_posts]
        likes_counts = {item['postId']: item['count'] for item in PostLike.objects.filter(postId__in=post_ids).values('postId').annotate(count=Count('postId'))}
        comments_counts = {item['postId']: item['count'] for item in PostComment.objects.filter(postId__in=post_ids).values('postId').annotate(count=Count('postId'))}
        saves_counts = {item['postId']: item['count'] for item in PostSave.objects.filter(postId__in=post_ids).values('postId').annotate(count=Count('postId'))}
        
        # Add counts to posts
        for post in feed_posts:
            post.likes_count = likes_counts.get(post.postId, 0)
            post.comments_count = comments_counts.get(post.postId, 0)
            post.saves_count = saves_counts.get(post.postId, 0)
        
        # Apply custom ranking
        def calculate_post_score(post):
            score = 0
            
            # Recency score (posts from last 24h get boost)
            hours_ago = (timezone.now() - post.timestamp).total_seconds() / 3600
            if hours_ago < 24:
                score += 100 - hours_ago
            
            # Following boost
            if post.userId in following_ids:
                score += 500
            
            # Location boost (same pincode)
            if post.pincode and post.pincode == user_pincode:
                score += 200
            
            # Engagement score
            score += post.likes_count * 2
            score += post.comments_count * 3
            score += post.saves_count * 5
            
            return score
        
        # Sort by score
        feed_posts.sort(key=calculate_post_score, reverse=True)
        
        # Step 6: Pagination
        start_idx = page_id * limit
        end_idx = start_idx + limit
        
        paginated_posts = feed_posts[start_idx:end_idx]
        has_more = len(feed_posts) > end_idx
        
        # Step 7: Build Feed Snippets
        results = []
        
        # Get all user IDs from posts to fetch user data in bulk
        post_user_ids = [post.userId for post in paginated_posts]
        users_map = {
            user.userId: user 
            for user in UserProfile.objects.filter(userId__in=post_user_ids)
        }
        
        # Get current user's engagement states for all posts in bulk
        post_ids = [post.postId for post in paginated_posts]
        user_liked_posts = set(
            PostLike.objects.filter(userId=user_id, postId__in=post_ids).values_list('postId', flat=True)
        )
        user_saved_posts = set(
            PostSave.objects.filter(userId=user_id, postId__in=post_ids).values_list('postId', flat=True)
        )
        
        for post in paginated_posts:
            # Get post author
            author = users_map.get(post.userId)
            if not author:
                continue  # Skip if author not found
            
            # Build snippet
            snippet = self._build_post_card_snippet_type_1(
                post=post,
                author=author,
                current_user=current_user,
                is_liked=post.postId in user_liked_posts,
                is_saved=post.postId in user_saved_posts
            )
            
            results.append({
                'type': 'POST_CARD_SNIPPET_TYPE_1',
                'post_card_snippet_type_1': snippet
            })
        
        # Step 8: Response Assembly
        return Response({
            'results': results,
            'has_more': has_more
        }, status=status.HTTP_200_OK)
    
    def _build_post_card_snippet_type_1(self, post, author, current_user, is_liked, is_saved):
        """
        Build POST_CARD_SNIPPET_TYPE_1 snippet structure
        
        Structure:
        - top_container (author info, badge, timestamp)
        - middle_container (image, caption)
        - bottom_container (actions, engagement counts)
        """
        
        # Calculate aspect ratio from location data if available
        aspect_ratio = 1.0  # Default square
        try:
            if post.location and isinstance(post.location, dict):
                # Placeholder - actual ratio should come from media metadata
                aspect_ratio = 1.0
        except:
            aspect_ratio = 1.0
        
        # Truncate caption if too long
        max_caption_length = 200
        caption = post.description or ""
        is_truncated = len(caption) > max_caption_length
        if is_truncated:
            caption = caption[:max_caption_length] + "..."
        
        # Determine if current user can edit this post
        can_edit = current_user.userId == post.userId
        
        # Badge logic (e.g., verified badge, location badge)
        badge = None
        if author.idCardUrl:  # Assuming verified users have ID card
            badge = {
                'type': 'verified',
                'icon': '✓'
            }
        
        # Get engagement counts safely
        likes_count = getattr(post, 'likes_count', 0)
        comments_count = getattr(post, 'comments_count', 0)
        saves_count = getattr(post, 'saves_count', 0)
        
        # Build snippet
        snippet = {
            'top_container': {
                'author': {
                    'user_id': author.userId,
                    'name': author.name or 'User',
                    'avatar': author.profilePhoto or 'https://via.placeholder.com/150',
                    'is_verified': badge is not None
                },
                'badge': badge,
                'timestamp': post.timestamp.isoformat(),
                'location': {
                    'pincode': post.pincode,
                    'city': None,  # Could be resolved from pincode if needed
                    'state': None
                }
            },
            'middle_container': {
                'media': {
                    'type': post.mediaType,
                    'url': post.mediaURL,
                    'aspect_ratio': aspect_ratio,
                    'thumbnail_url': post.mediaURL  # Same as main for now
                },
                'caption': {
                    'text': caption,
                    'is_truncated': is_truncated,
                    'full_text': post.description or ""
                }
            },
            'bottom_container': {
                'engagement': {
                    'likes_count': likes_count,
                    'comments_count': comments_count,
                    'saves_count': saves_count
                },
                'actions': {
                    'can_like': True,
                    'can_comment': True,
                    'can_save': True,
                    'can_share': True,
                    'can_edit': can_edit,
                    'can_report': not can_edit
                },
                'user_state': {
                    'is_liked': is_liked,
                    'is_saved': is_saved
                }
            },
            'meta': {
                'post_id': post.postId,
                'author_id': post.userId,
                'created_at': post.timestamp.isoformat()
            }
        }
        
        return snippet
