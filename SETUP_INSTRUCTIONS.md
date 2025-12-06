# Django Social App API - Setup Instructions

## ⚠️ DATABASE CONNECTION ISSUE

The application is fully built with all models, serializers, views, and endpoints, but we're encountering a database connection issue with Supabase.

### Error Message:
```
FATAL: Tenant or user not found
```

### Possible Solutions:

1. **Check Supabase Database Settings:**
   - Go to: https://supabase.com/dashboard/project/khudodonuubcqupqskxr/settings/database
   - Verify the connection details:
     - Host
     - Port
     - Database name
     - User
     - Password

2. **Enable Direct Database Access:**
   - In Supabase Dashboard > Settings > Database
   - Enable "Enable direct connection to database"
   - Check if there's an IP allowlist
   - Add your IP or allow all IPs (0.0.0.0/0) for testing

3. **Get Correct Connection String:**
   - In Supabase Dashboard, look for "Connection String"
   - It should be in format: `postgresql://postgres.[REF]:[PASSWORD]@[HOST]:5432/postgres`

### Current Settings (in `/Users/vishaljha/backend/backend/settings.py`):

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres.khudodonuubcqupqskxr",  # ← May need adjustment
        "PASSWORD": "YA56ec3QY4C5uz7W",
        "HOST": "aws-0-ap-south-1.pooler.supabase.com",  # ← May need adjustment
        "PORT": "5432",  # ← May be 6543 for transaction pooling
    }
}
```

### To Update Database Settings:

Edit `/Users/vishaljha/backend/backend/settings.py` lines 83-98 with the correct values from your Supabase dashboard.

---

## 📁 COMPLETED IMPLEMENTATION

All files have been created successfully:

### Models (`/Users/vishaljha/backend/api/models.py`)
✅ UserProfile - with all fields (userId, name, gender, age, bio, email, etc.)
✅ FollowRequest - (fromUserId, toUserId, status)
✅ Follower - (followerId, followingId)
✅ Post - with nested location JSON field
✅ Story - with expiration support
✅ Chat - (users array, lastMessage, lastMessageTime)
✅ Message - (chatId, senderId, content, timestamp)

### Serializers (`/Users/vishaljha/backend/api/serializers.py`)
✅ All model serializers with proper field handling
✅ PostLocationSerializer for nested location data
✅ ChatWithMessagesSerializer for chat with messages

### Views (`/Users/vishaljha/backend/api/views.py`)
✅ UserProfileViewSet - GET /users/{userId}, /users/{userId}/following, /users/{userId}/followers
✅ FollowRequestViewSet - GET/POST/PATCH /followRequests/{documentId}
✅ FollowerViewSet - GET /followers/{documentId}
✅ PostViewSet - GET/POST /posts/{postId}
✅ UserPostsView - GET /users/{userId}/posts
✅ StoryViewSet - GET/POST /stories/{storyId}
✅ UserStoriesView - GET /users/{userId}/stories (filters expired)
✅ ChatViewSet - GET/POST /chats/{chatId}
✅ ChatMessagesView - GET/POST /chats/{chatId}/messages (auto-updates lastMessage)

### URLs (`/Users/vishaljha/backend/api/urls.py`)
✅ All endpoints configured with Django REST Router
✅ Custom URL patterns for user-specific endpoints

### Utils (`/Users/vishaljha/backend/api/utils.py`)
✅ create_follower_relationship() - Auto-creates follower when request accepted
✅ Automatically updates UserProfile followers/following arrays

---

## 🚀 ONCE DATABASE IS CONNECTED:

### 1. Run Migrations
```bash
cd /Users/vishaljha/backend
python manage.py migrate
```

### 2. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 3. Run Server
```bash
python manage.py runserver
```

### 4. Test Endpoints

Server will be at: `http://127.0.0.1:8000/`

#### Available Endpoints:
- `GET /users/{userId}/` - Get user profile
- `GET /users/{userId}/following/` - Get following list
- `GET /users/{userId}/followers/` - Get followers list
- `GET /users/{userId}/posts/` - Get user's posts
- `GET /users/{userId}/stories/` - Get active stories
- `POST /followRequests/` - Create follow request
- `PATCH /followRequests/{documentId}/` - Update follow request (auto-creates follower on accept)
- `GET /followers/{documentId}/` - Get follower relationship
- `POST /posts/` - Create post with location
- `GET /posts/{postId}/` - Get post
- `POST /stories/` - Create story
- `GET /stories/{storyId}/` - Get story
- `POST /chats/` - Create chat
- `GET /chats/{chatId}/` - Get chat
- `POST /chats/{chatId}/messages/` - Send message (auto-updates chat)
- `GET /chats/{chatId}/messages/` - Get messages

---

## 📝 NEXT STEPS:

1. **Fix Database Connection** - Update settings with correct Supabase credentials
2. **Run Migrations** - `python manage.py migrate`
3. **Test Each Endpoint** - Use Postman, curl, or Django REST Framework browsable API
4. **Add Authentication** (if needed) - JWT tokens, session auth, etc.
5. **Add Permissions** (if needed) - User-specific access controls

---

## 🛠️ Installed Dependencies:

All required packages are installed:
- Django==5.0
- djangorestframework==3.14.0
- django-cors-headers==4.3.1
- psycopg2-binary==2.9.10
- python-dotenv==1.0.0
