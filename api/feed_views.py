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
        
        New Structure:
        - top_container (left: avatar/title/badge/meta_row, right: menu_icon)
        - middle_container (image only)
        - bottom_container (caption, actions_row)
        """
        
        from django.utils import timezone
        import math
        
        # Calculate time ago
        now = timezone.now()
        time_diff = now - post.timestamp
        hours_ago = time_diff.total_seconds() / 3600
        
        if hours_ago < 1:
            time_text = f"{int(time_diff.total_seconds() / 60)}m"
        elif hours_ago < 24:
            time_text = f"{int(hours_ago)}h"
        else:
            days_ago = int(hours_ago / 24)
            time_text = f"{days_ago}d"
        
        # Calculate aspect ratio
        aspect_ratio = 1.0  # Default square
        try:
            if post.location and isinstance(post.location, dict):
                # For now, assume 4:3 aspect ratio for images
                aspect_ratio = 1.333
        except:
            aspect_ratio = 1.0
        
        # Badge logic - Local Expert for verified users or location-based
        badge = None
        if author.idCardUrl:  # Verified user
            badge = {
                "text": "Verified",
                "style": {
                    "radius": 10,
                    "backgroundColor": "#FFE7E7",
                    "textColor": "#B00020",
                    "fontSize": 10,
                    "fontWeight": "700"
                }
            }
        elif post.pincode == current_user.pincode:  # Local user
            badge = {
                "text": "Local",
                "style": {
                    "radius": 10,
                    "backgroundColor": "#E7F3FF",
                    "textColor": "#0066CC",
                    "fontSize": 10,
                    "fontWeight": "700"
                }
            }
        
        # Build snippet with new structure
        snippet = {
            'top_container': {
                'left': {
                    'avatar': {
                        'url': author.profilePhoto or 'https://i.pravatar.cc/150?img=5',
                        'width': 72,
                        'height': 72,
                        'aspectRatio': 1,
                        'style': {'size': 36, 'radius': 18}
                    },
                    'title': {
                        'text': author.name or 'User',
                        'style': {'fontSize': 14, 'fontWeight': '700', 'color': '#111111'}
                    },
                    'badge': badge,
                    'meta_row': {
                        'icon': {'name': 'location-outline', 'size': 14, 'color': '#111111'},
                        'text': {'text': post.pincode or 'Unknown', 'style': {'fontSize': 11, 'color': '#111111', 'opacity': 0.6}},
                        'separator': {'text': '•', 'style': {'fontSize': 11, 'color': '#111111', 'opacity': 0.6}},
                        'time': {'text': time_text, 'style': {'fontSize': 11, 'color': '#111111', 'opacity': 0.6}},
                        'gap': 6
                    }
                },
                'right': {
                    'menu_icon': {
                        'name': 'ellipsis-vertical',
                        'size': 18,
                        'color': '#111111'
                    }
                }
            },
            'middle_container': {
                'image': {
                    'url': post.mediaURL,
                    'width': 1200,
                    'height': 800,
                    'aspectRatio': aspect_ratio,
                    'style': {'radius': 0, 'resizeMode': 'cover'}
                }
            },
            'bottom_container': {
                'caption': {
                    'text': post.description or '',
                    'style': {'fontSize': 12.5, 'lineHeight': 18, 'color': '#111111', 'opacity': 0.85},
                    'truncate': {
                        'enabled': True,
                        'maxChars': 80,
                        'moreText': 'Read More…',
                        'lessText': 'Read less',
                        'style': {'fontWeight': '700', 'opacity': 0.7, 'color': '#B00020'}
                    }
                },
                'actions_row': {
                    'left_actions': [
                        {
                            'id': 'like',
                            'icon': {
                                'name': 'heart-outline',
                                'activeName': 'heart',
                                'size': 22,
                                'color': '#111111',
                                'activeColor': '#E11D48'
                            },
                            'active': is_liked
                        },
                        {
                            'id': 'comment',
                            'icon': {'name': 'chatbubble-outline', 'size': 21, 'color': '#111111'}
                        },
                        {
                            'id': 'share',
                            'icon': {'name': 'paper-plane-outline', 'size': 21, 'color': '#111111'}
                        }
                    ],
                    'right_actions': [
                        {
                            'id': 'save',
                            'icon': {
                                'name': 'bookmark-outline',
                                'activeName': 'bookmark',
                                'size': 21,
                                'color': '#111111',
                                'activeColor': '#111111'
                            },
                            'active': is_saved
                        }
                    ]
                }
            }
        }
        
        return snippet
