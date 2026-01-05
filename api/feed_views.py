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

    Returns filtered posts in the user's home feed with pagination
    Request body: {"filters": ["entertainment", "sports"], "page_id": "", "limit": 10}
    Requires authentication
    """

    def post(self, request):
        """
        Return the exact structure from expect.json
        Requires authentication
        """
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

        # Step 2: Parse request parameters for filtering and pagination
        filters = request.data.get('filters', [])
        page_id = request.data.get('page_id', '')
        limit = request.data.get('limit', 10)
        
        # Validate limit
        try:
            limit = int(limit)
            if limit < 1 or limit > 50:
                limit = 10  # Default to 10 if invalid
        except (ValueError, TypeError):
            limit = 10
        
        # Step 3: Fetch posts for the home feed
        # Start with base queryset
        posts_query = Post.objects.all()
        
        # Apply filters if provided
        if filters:
            # Map filter names to post types
            filter_mapping = {
                'entertainment': ['post'],
                'sports': ['post'],
                'questions': ['question'],
                'alerts': ['alert'],
                'recommendations': ['recommendation']
            }
            
            # Collect all post types from filters
            post_types = []
            for filter_name in filters:
                if filter_name in filter_mapping:
                    post_types.extend(filter_mapping[filter_name])
            
            # If we have valid post types, filter by them
            if post_types:
                posts_query = posts_query.filter(post_type__in=post_types)
        
        # Apply pagination
        if page_id:
            try:
                # page_id is the postId to start after
                start_post = Post.objects.get(postId=int(page_id))
                posts_query = posts_query.filter(timestamp__lt=start_post.timestamp)
            except (Post.DoesNotExist, ValueError):
                # If invalid page_id, ignore pagination
                pass
        
        # Order by timestamp and limit results
        posts = posts_query.order_by('-timestamp')[:limit]
        
        # Format posts for the feed
        feed_posts = []
        for post in posts:
            # Get user profile for the post author
            try:
                post_user = UserProfile.objects.get(userId=post.userId)
                author_name = post_user.name or f"User {post.userId[:8]}"
            except UserProfile.DoesNotExist:
                author_name = f"User {post.userId[:8]}"
            
            feed_posts.append({
                'postId': post.postId,
                'post_type': post.post_type,
                'author': {
                    'userId': post.userId,
                    'name': author_name
                },
                'content': post.description or '',
                'mediaType': post.mediaType,
                'mediaURL': post.mediaURL,
                'pincode': post.pincode,
                'timestamp': post.timestamp.isoformat(),
                'location': post.location or {}
            })
        
        return Response({
            'results': [{
                'type': 'HOME_FEED_V1',
                'home_feed_v1': {
                    'posts': feed_posts,
                    'total_count': len(feed_posts),
                    'filters_applied': filters,
                    'limit': limit,
                    'next_page_id': feed_posts[-1]['postId'] if feed_posts else None
                }
            }]
        }, status=status.HTTP_200_OK)

class CreatePostView(APIView):
    """
    PUT /create-post - Returns the UI schema for the create post screen
    POST /create-post - Creates a new post with provided data

    Both methods require authentication
    """

    def put(self, request):
        """
        Return the exact structure from expect.json
        Requires authentication
        """
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

        # Check if user is guest (guests shouldn't access create post)
        if current_user.is_guest:
            return Response({
                'error': {
                    'code': 'ACCESS_DENIED',
                    'message': 'Guest users cannot create posts'
                }
            }, status=status.HTTP_403_FORBIDDEN)

        # Return the exact structure from expect.json
        return Response({
            "results": [{
                "type": "CREATE_POST_SCREEN_V1",
                "create_post_screen_v1": {
                    "header": {
                        "leftIcon": {"name": "add", "size": 18, "color": "#FF4F9A"},
                        "title": {
                            "text": "Create Post",
                            "style": {"fontSize": 18, "fontWeight": "700", "color": "#2B1B3F"}
                        }
                    },
                    "fields": {
                        "shareType": {
                            "label": {
                                "text": "What do you want to share?*",
                                "style": {"fontSize": 14, "fontWeight": "600", "color": "#000000"}
                            },
                            "required": True,
                            "placeholder": {
                                "text": "Select",
                                "style": {"fontSize": 16, "fontWeight": "500", "color": "#000000"}
                            },
                            "rightIcon": {"name": "chevron-down", "size": 18, "color": "#666"},
                            "options": [
                                {"id": "post", "label": "Post", "displayLabel": "Post An Update"},
                                {"id": "question", "label": "Question"},
                                {"id": "alert", "label": "Alert"},
                                {"id": "recommendation", "label": "Recommendation"}
                            ]
                        },
                        "postText": {
                            "label": {
                                "text": "Write your post*",
                                "style": {"fontSize": 14, "fontWeight": "500", "color": "#000000"}
                            },
                            "required": True,
                            "placeholder": {
                                "text": "What would you like to share with your community?",
                                "style": {"fontSize": 16, "fontWeight": "500", "color": "#9C9C9C"}
                            },
                            "maxChars": 500,
                            "helperText": {
                                "text": "Max 500 characters",
                                "style": {"fontSize": 12, "fontWeight": "500", "color": "#9C9C9C"}
                            },
                            "style": {
                                "containerRadius": 14,
                                "borderColor": "#E0E0E0",
                                "borderWidth": 1.3,
                                "minHeight": 124,
                                "backgroundColor": "#FFFFFF"
                            }
                        },
                        "photo": {
                            "label": {
                                "text": "Add Photo (Optional)",
                                "style": {"fontSize": 14, "fontWeight": "600", "color": "#000000"}
                            },
                            "dashed": True,
                            "maxSizeText": {
                                "text": "(up to 5mb)",
                                "style": {"fontSize": 11, "color": "#AAA"}
                            },
                            "icon": {"name": "cloud-upload-outline", "size": 22, "color": "#777"},
                            "action": {
                                "id": "upload_photo",
                                "icon": {"name": "cloud-upload-outline", "size": 22, "color": "#777"}
                            },
                            "style": {
                                "radius": 14,
                                "borderColor": "#A0A0A0",
                                "borderWidth": 1.5,
                                "backgroundColor": "#FFFFFF",
                                "height": 124
                            },
                            "mock_uploaded_image": {
                                "url": "https://picsum.photos/800/800",
                                "aspectRatio": 1,
                                "style": {"resizeMode": "cover"}
                            }
                        },
                        "pincode": {
                            "label": {
                                "text": "Select Pincode*",
                                "style": {"fontSize": 14, "fontWeight": "600", "color": "#000000"}
                            },
                            "required": True,
                            "options": [
                                {
                                    "id": "pincode_home_201301",
                                    "leftIcon": {"name": "home-outline", "size": 16, "color": "#111"},
                                    "pincodeText": {
                                        "text": "201301",
                                        "style": {"fontSize": 16, "fontWeight": "600", "color": "#000000"}
                                    },
                                    "tagText": {
                                        "text": "• HOME",
                                        "style": {"fontSize": 12, "fontWeight": "600", "color": "#00FF48"}
                                    },
                                    "subtitleText": {
                                        "text": "Sector 62 Noida",
                                        "style": {"fontSize": 12, "fontWeight": "400", "color": "#9C9C9C"}
                                    },
                                    "selected": True
                                },
                                {
                                    "id": "pincode_office_221512",
                                    "leftIcon": {"name": "briefcase-outline", "size": 16, "color": "#111"},
                                    "pincodeText": {
                                        "text": "221512",
                                        "style": {"fontSize": 16, "fontWeight": "600", "color": "#000000"}
                                    },
                                    "tagText": {
                                        "text": "• OFFICE",
                                        "style": {"fontSize": 12, "fontWeight": "600", "color": "#FF4F9A"}
                                    },
                                    "subtitleText": {
                                        "text": "Metro Station, Noida",
                                        "style": {"fontSize": 12, "fontWeight": "400", "color": "#9C9C9C"}
                                    }
                                }
                            ]
                        }
                    },
                    "footer": {
                        "primaryButton": {
                            "text": {
                                "text": "Post",
                                "style": {"fontSize": 18, "fontWeight": "700", "color": "#2B1C3F"}
                            },
                            "action": {
                                "id": "submit_post",
                                "icon": {"name": "send-outline", "size": 18, "color": "#111"}
                            },
                            "style": {
                                "height": 58,
                                "radius": 14,
                                "backgroundColor": "#D8FF2F",
                                "disabledBackgroundColor": "#EDEAF2"
                            }
                        }
                    },
                    "entity_keys": {
                        "typeKey": "post_type",
                        "textKey": "content",
                        "pincodeKey": "pincode_id",
                        "photoKey": "photo_url"
                    }
                }
            }]
        })


    def post(self, request):
        """
        Create a new post with the provided data
        Requires authentication
        """
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

        # Check if user is guest (guests shouldn't create posts)
        if current_user.is_guest:
            return Response({
                'error': {
                    'code': 'ACCESS_DENIED',
                    'message': 'Guest users cannot create posts'
                }
            }, status=status.HTTP_403_FORBIDDEN)

        # Step 2: Request Validation
        post_type = request.data.get('post_type')
        content = request.data.get('content', '').strip()
        pincode_id = request.data.get('pincode_id')
        photo_url = request.data.get('photo_url')

        # Validate post_type
        valid_types = ['post', 'question', 'alert', 'recommendation']
        if not post_type or post_type not in valid_types:
            return Response({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': f'post_type is required and must be one of: {", ".join(valid_types)}'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate content (required)
        if not content:
            return Response({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'content is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate content length (max 500 chars)
        if len(content) > 500:
            return Response({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'content must not exceed 500 characters'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate pincode_id (required)
        if not pincode_id:
            return Response({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'pincode_id is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Parse pincode from pincode_id (format: pincode_home_201301 or pincode_office_221512)
        try:
            pincode_parts = pincode_id.split('_')
            if len(pincode_parts) >= 3 and pincode_parts[0] == 'pincode':
                pincode = pincode_parts[-1]  # Last part is the actual pincode
            else:
                return Response({
                    'error': {
                        'code': 'INVALID_REQUEST',
                        'message': 'Invalid pincode_id format'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        except (IndexError, AttributeError):
            return Response({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Invalid pincode_id format'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate pincode format (6 digits)
        if not pincode.isdigit() or len(pincode) != 6:
            return Response({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Invalid pincode format'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Step 3: Create the post
        try:
            # Determine media type and URL
            if photo_url:
                media_type = 'image'
                media_url = photo_url
            else:
                media_type = 'image'  # Default to image type
                media_url = 'https://via.placeholder.com/1x1/ffffff/ffffff'  # Placeholder for text posts

            # Create the post
            post = Post.objects.create(
                userId=user_id,
                post_type=post_type,                description=content,
                mediaType=media_type,
                mediaURL=media_url,
                pincode=pincode,
                location={}  # Empty location object for now
            )

            return Response({
                'entities': {
                    'post_type': post_type,
                    'content': content,
                    'pincode_id': pincode_id,
                    'photo_url': photo_url if photo_url else None
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to create post'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SavePostView(APIView):
    """
    POST /save-post

    Saves a new post with validation
    Requires authentication
    """
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

        # Check if user is guest (guests shouldn't create posts)
        if current_user.is_guest:
            return Response({
                'error': {
                    'code': 'ACCESS_DENIED',
                    'message': 'Guest users cannot create posts'
                }
            }, status=status.HTTP_403_FORBIDDEN)

        # Step 2: Request Validation
        post_type = request.data.get('post_type')
        content = request.data.get('content', '').strip()
        pincode_id = request.data.get('pincode_id')
        photo_url = request.data.get('photo_url')

        # Validate post_type
        valid_types = ['post', 'question', 'alert', 'recommendation']
        if not post_type or post_type not in valid_types:
            return Response({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': f'post_type is required and must be one of: {", ".join(valid_types)}'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate content (required)
        if not content:
            return Response({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'content is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate content length (max 500 chars)
        if len(content) > 500:
            return Response({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'content must not exceed 500 characters'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate pincode_id (required)
        if not pincode_id:
            return Response({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'pincode_id is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Parse pincode from pincode_id (format: pincode_home_201301 or pincode_office_221512)
        try:
            pincode_parts = pincode_id.split('_')
            if len(pincode_parts) >= 3 and pincode_parts[0] == 'pincode':
                pincode = pincode_parts[-1]  # Last part is the actual pincode
            else:
                return Response({
                    'error': {
                        'code': 'INVALID_REQUEST',
                        'message': 'Invalid pincode_id format'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        except (IndexError, AttributeError):
            return Response({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Invalid pincode_id format'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate pincode format (6 digits)
        if not pincode.isdigit() or len(pincode) != 6:
            return Response({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Invalid pincode format'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Step 3: Create the post
        try:
            # Determine media type and URL
            if photo_url:
                media_type = 'image'
                media_url = photo_url
            else:
                media_type = 'image'  # Default to image type
                media_url = 'https://via.placeholder.com/1x1/ffffff/ffffff'  # Placeholder for text posts

            # Create the post
            post = Post.objects.create(
                userId=user_id,
                post_type=post_type,                description=content,
                mediaType=media_type,
                mediaURL=media_url,
                pincode=pincode,
                location={}  # Empty location object for now
            )

            return Response({
                'entities': {
                    'post_type': post_type,
                    'content': content,
                    'pincode_id': pincode_id,
                    'photo_url': photo_url if photo_url else None
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to create post'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
