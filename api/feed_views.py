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
    Request body: {"filters": ["entertainment", "sports"], "page_id": "", "limit": 10, "pin_code": "560034"}
    Supports authenticated users, guest users with PIN, and guest users without PIN
    """

    def _get_pin_scoped_feed(self, user, pin_code, filters, page_id, limit):
        """Generate PIN-scoped personal feed for authenticated users"""
        posts_query = Post.objects.all()
        
        # PIN Code = Feed Namespace: Filter posts by PIN code
        # Users in the same PIN see each other's posts (shared feed room)
        posts_query = posts_query.filter(pincode=pin_code)
        
        # Apply filters if provided
        if filters:
            filter_mapping = {
                'entertainment': ['post'],
                'sports': ['post'],
                'questions': ['question'],
                'alerts': ['alert'],
                'recommendations': ['recommendation']
            }
            
            post_types = []
            for filter_name in filters:
                if filter_name in filter_mapping:
                    post_types.extend(filter_mapping[filter_name])
            
            if post_types:
                posts_query = posts_query.filter(post_type__in=post_types)
        
        # Apply pagination
        if page_id:
            try:
                start_post = Post.objects.get(postId=int(page_id))
                posts_query = posts_query.filter(timestamp__lt=start_post.timestamp)
            except (Post.DoesNotExist, ValueError):
                pass
        
        # PIN-scoped feed: deterministic ordering within the PIN namespace
        # Same PIN = same feed ordering for all users
        pin_hash = hash(pin_code) % 1000  # Deterministic seed based on PIN
        return posts_query.order_by('-timestamp')[:limit]

    def _get_pin_scoped_feed(self, user, user_pincodes, filters, page_id, limit):
        """Generate PIN-scoped personal feed for authenticated users"""
        posts_query = Post.objects.all()
        
        # PIN Codes = Feed Namespaces: Filter posts by any of user's PIN codes
        # Users see posts from all their associated PIN codes (multiple shared feed rooms)
        posts_query = posts_query.filter(pincode__in=user_pincodes)
        
        # Apply filters if provided
        if filters:
            filter_mapping = {
                'entertainment': ['post'],
                'sports': ['post'],
                'questions': ['question'],
                'alerts': ['alert'],
                'recommendations': ['recommendation']
            }
            
            post_types = []
            for filter_name in filters:
                if filter_name in filter_mapping:
                    post_types.extend(filter_mapping[filter_name])
            
            if post_types:
                posts_query = posts_query.filter(post_type__in=post_types)
        
        # Apply pagination
        if page_id:
            try:
                start_post = Post.objects.get(postId=int(page_id))
                posts_query = posts_query.filter(timestamp__lt=start_post.timestamp)
            except (Post.DoesNotExist, ValueError):
                pass
        
        # PIN-scoped feed: deterministic ordering within the PIN namespaces
        # Same PIN codes = same feed ordering for all users in those PIN groups
        pin_hash = hash(str(sorted(user_pincodes))) % 1000  # Deterministic seed based on PIN codes
        return posts_query.order_by('-timestamp')[:limit]

    def _get_random_exploratory_feed(self, user, filters, page_id, limit):
        """Generate random exploratory feed for authenticated users without PIN"""
        posts_query = Post.objects.all()
        
        # Apply filters if provided
        if filters:
            filter_mapping = {
                'entertainment': ['post'],
                'sports': ['post'],
                'questions': ['question'],
                'alerts': ['alert'],
                'recommendations': ['recommendation']
            }
            
            post_types = []
            for filter_name in filters:
                if filter_name in filter_mapping:
                    post_types.extend(filter_mapping[filter_name])
            
            if post_types:
                posts_query = posts_query.filter(post_type__in=post_types)
        
        # Apply pagination
        if page_id:
            try:
                start_post = Post.objects.get(postId=int(page_id))
                posts_query = posts_query.filter(timestamp__lt=start_post.timestamp)
            except (Post.DoesNotExist, ValueError):
                pass
        
        # Random exploratory feed: user-specific randomization
        # Each user gets a different random ordering for exploration
        user_seed = hash(user.userId) % 1000  # Deterministic seed per user
        return posts_query.order_by('?')[:limit]

    def post(self, request):
        """
        Return home feed based on PIN codes from user profile:
        - Authenticated user with PIN codes in profile: PIN-scoped personal feed (sees posts from all their PIN codes)
        - Authenticated user without PIN codes in profile: Random/exploratory feed
        
        PIN Codes = Feed Namespaces (shared feed rooms/content visibility scopes)
        Authentication token is the ONLY input. PIN codes are fetched from DB and used ONLY for feed recommendation/matching.
        No extra client responsibility - PIN codes are managed server-side.
        """
        # Authentication is ALWAYS required
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return Response({
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication credentials were not provided'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.replace('Bearer ', '').strip()
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            current_user = UserProfile.objects.get(userId=user_id)
        except Exception:
            return Response({
                'error': {
                    'code': 'INVALID_TOKEN',
                    'message': 'Invalid or expired authentication token'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Parse request parameters
        filters = request.data.get('filters', [])
        page_id = request.data.get('page_id', '')
        limit = request.data.get('limit', 10)
        
        # PIN codes are fetched from authenticated user's profile (stored in DB)
        # Users can have multiple PIN codes (main, home, office, active, additional)
        user_pincodes = []
        if current_user.pincode:
            user_pincodes.append(current_user.pincode)
        if current_user.home_pincode:
            user_pincodes.append(current_user.home_pincode)
        if current_user.office_pincode:
            user_pincodes.append(current_user.office_pincode)
        if current_user.activePincodes:
            user_pincodes.extend(current_user.activePincodes)
        if current_user.additional_pincodes:
            user_pincodes.extend(current_user.additional_pincodes)
        
        # Remove duplicates
        user_pincodes = list(set(user_pincodes))
        
        try:
            limit = int(limit)
            if limit < 1 or limit > 50:
                limit = 10 
        except (ValueError, TypeError):
            limit = 10
        
        # Determine feed type based on user's PIN codes
        if user_pincodes:
            # A. Authenticated user with PIN codes: PIN-scoped personal feed
            # Users see posts from any of their associated PIN codes (multiple shared feed rooms)
            posts = self._get_pin_scoped_feed(current_user, user_pincodes, filters, page_id, limit)
        else:
            # B. Authenticated user with no PIN codes: Random/exploratory feed
            posts = self._get_random_exploratory_feed(current_user, filters, page_id, limit)
        
        # Determine if there are more posts available
        has_more = len(posts) == limit
        
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
        
        # Home screen header structure
        header = {
            "type": "HOME_SCREEN_HEADER_V1",
            "home_screen_header_v1": {
                "containerStyle": {
                    "backgroundColor": "#FFFFFF"
                },
                "top_row": {
                    "location": {
                        "leftIcon": {
                            "name": "location-outline",
                            "size": 18,
                            "color": "#2B1B3F"
                        },
                        "primary": {
                            "text": user_pincodes[0] if user_pincodes else "202024",  # Show first PIN if available
                            "style": {
                                "fontSize": 16,
                                "fontWeight": "600",
                                "color": "background: #000000;",
                                "opacity": 1
                            }
                        },
                        "dropdownIcon": {
                            "name": "chevron-down",
                            "size": 16,
                            "color": "#111111"
                        },
                        "secondary": {
                            "text": "Sector 26, SG Road, Noida",
                            "style": {
                                "fontSize": 14,
                                "fontWeight": "400",
                                "color": "background: #A6A6A6;",
                                "opacity": 0.45
                            }
                        }
                    },
                    "actions": [
                        {
                            "id": "chat",
                            "icon": {
                                "name": "chatbubble-outline",
                                "size": 18,
                                "color": "#2B1B3F"
                            },
                            "active": False,
                            "disabled": False
                        },
                        {
                            "id": "notifications",
                            "icon": {
                                "name": "notifications-outline",
                                "size": 18,
                                "color": "#141B34"
                            },
                            "active": True,
                            "disabled": False
                        }
                    ]
                },
                "search": {
                    "leftIcon": {
                        "name": "search-outline",
                        "size": 18,
                        "color": "#141B34"
                    },
                    "placeholder": "Near by people...",
                    "placeholderStyle": {
                        "color": "rgba(17,17,17,0.35)"
                    },
                    "inputStyle": {
                        "fontSize": 16,
                        "fontWeight": "500",
                        "color": "#A6A6A6",
                        "opacity": 1
                    },
                    "containerStyle": {
                        "backgroundColor": "#FFFFFF",
                        "border": {
                            "width": 1,
                            "height": 44,
                            "color": "#E8E8E8",
                            "radius": 12,
                            "style": "solid"
                        }
                    },
                    "value": ""
                },
                "filters_row": {
                    "chips": [
                        {
                            "id": "all",
                            "label": {
                                "text": "All",
                                "style": {
                                    "fontSize": 14,
                                    "fontWeight": "700",
                                    "color": "#111111"
                                }
                            },
                            "selected": True,
                            "containerStyle": {
                                "backgroundColor": "#FFFFFF",
                                "border": { "width": 1.3, "color": "#E0E0E0", "radius": 14 }
                            },
                            "selectedContainerStyle": {
                                "backgroundColor": "#111111",
                                "border": { "width": 1.3, "color": "#263238", "radius": 14 }
                            }
                        },
                        {
                            "id": "posts",
                            "icon": { "name": "flash-outline", "size": 16, "color": "#111111" },
                            "label": {
                                "text": "Posts",
                                "style": { "fontSize": 14, "fontWeight": "700", "color": "#111111" }
                            },
                            "containerStyle": {
                                "backgroundColor": "#FFFFFF",
                                "border": { "width": 1.3, "color": "#E0E0E0", "radius": 14 }
                            },
                            "selectedContainerStyle": {
                                "backgroundColor": "#111111",
                                "border": { "width": 1.3, "color": "#263238", "radius": 14 }
                            }
                        },
                        {
                            "id": "people",
                            "icon": { "name": "person-outline", "size": 16, "color": "#111111" },
                            "label": {
                                "text": "People",
                                "style": { "fontSize": 14, "fontWeight": "700", "color": "#111111" }
                            },
                            "containerStyle": {
                                "backgroundColor": "#FFFFFF",
                                "border": { "width": 1.3, "color": "#E0E0E0", "radius": 14 }
                            },
                            "selectedContainerStyle": {
                                "backgroundColor": "#111111",
                                "border": { "width": 1.3, "color": "#263238", "radius": 14 }
                            }
                        },
                        {
                            "id": "business",
                            "icon": { "name": "briefcase-outline", "size": 16, "color": "#111111" },
                            "label": {
                                "text": "Business",
                                "style": { "fontSize": 14, "fontWeight": "700", "color": "#111111" }
                            },
                            "containerStyle": {
                                "backgroundColor": "#FFFFFF",
                                "border": { "width": 1.3, "color": "#E0E0E0", "radius": 14 }
                            },
                            "selectedContainerStyle": {
                                "backgroundColor": "#111111",
                                "border": { "width": 1.3, "color": "#263238", "radius": 14 }
                            }
                        }
                    ]
                }
            }
        }
        
        return Response({
            'results': feed_posts,
            'has_more': has_more,
            'header': header
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
        # if current_user.is_guest:
        #     return Response({
        #         'error': {
        #             'code': 'ACCESS_DENIED',
        #             'message': 'Guest users cannot access home feed'
        #         }
        #     }, status=status.HTTP_403_FORBIDDEN)

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
        # if current_user.is_guest:
        #     return Response({
        #         'error': {
        #             'code': 'ACCESS_DENIED',
        #             'message': 'Guest users cannot create posts'
        #         }
        #     }, status=status.HTTP_403_FORBIDDEN)

        # Step 2: Request Validation
        post_type = request.data.get('post_type')
        content = request.data.get('content', '').strip()
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
        # if current_user.is_guest:
        #     return Response({
        #         'error': {
        #             'code': 'ACCESS_DENIED',
        #             'message': 'Guest users cannot create posts'
        #         }
        # #     }, status=status.HTTP_403_FORBIDDEN)

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
