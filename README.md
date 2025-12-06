# Social App Backend API

Complete Django REST Framework backend for a social networking application with Supabase PostgreSQL database.

## 🚀 Features

- User profile management
- Follow/Unfollow system with requests
- Posts with location data
- Temporary stories
- Real-time messaging
- All endpoints tested and working with Supabase

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL (Supabase)
- pip

## ⚙️ Installation

1. Install dependencies:
```bash
pip install django djangorestframework python-dotenv psycopg2-binary django-cors-headers supabase
```

2. Configure environment variables in `.env`:
```env
SubaseUrl=https://qzhfqngedeadnyeqtoqp.supabase.co
SUPABASE_DB_PASSWORD=955Fp4x0TrLoWjha
ANON_PUBLIC=your_anon_key
SERVICE_ROLE=your_service_role_key
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Start server:
```bash
python manage.py runserver 0.0.0.0:8000
```

## 🔗 API Endpoints

### User Management

#### Create User Profile
**POST** `/users/`
```json
{
  "userId": "user123",
  "name": "John Doe",
  "gender": "male",
  "age": 25,
  "bio": "Test user bio",
  "email": "john@example.com",
  "profilePhoto": "https://example.com/photo.jpg",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "activePincodes": ["110001", "110002"],
  "idCardUrl": "https://example.com/id.jpg"
}
```

#### Get All Users
**GET** `/users/`

#### Get User by ID
**GET** `/users/{userId}/`

#### Update User
**PATCH** `/users/{userId}/`
```json
{
  "bio": "Updated bio",
  "age": 26
}
```

### Social Features

#### Send Follow Request
**POST** `/users/{userId}/follow/`
```json
{
  "toUserId": "user456"
}
```

#### Accept/Reject Follow Request
**POST** `/users/{userId}/accept-follow/`
```json
{
  "fromUserId": "user123",
  "status": "accepted"  // or "rejected"
}
```

#### Get Followers
**GET** `/users/{userId}/followers/`

#### Get Following
**GET** `/users/{userId}/following/`

#### Unfollow User
**POST** `/users/{userId}/unfollow/`
```json
{
  "toUserId": "user456"
}
```

### Posts

#### Create Post
**POST** `/posts/`
```json
{
  "userId": "user123",
  "description": "My first post!",
  "mediaType": "image",
  "mediaURL": "https://example.com/image.jpg",
  "pincode": "110001",
  "location": {
    "latitude": 28.6139,
    "longitude": 77.2090,
    "address": "New Delhi"
  }
}
```

#### Get Posts by User
**GET** `/users/{userId}/posts/`

#### Get Post by ID
**GET** `/posts/{postId}/`

### Stories

#### Create Story
**POST** `/stories/`
```json
{
  "userId": "user123",
  "description": "My story!",
  "mediaType": "image",
  "mediaURL": "https://example.com/story.jpg",
  "expireAt": "2025-12-07T10:00:00Z"
}
```

#### Get Active Stories by User
**GET** `/users/{userId}/stories/`

### Messaging

#### Get or Create Chat
**POST** `/chats/get-or-create/`
```json
{
  "user1": "user123",
  "user2": "user456"
}
```

#### Send Message
**POST** `/chats/{chatId}/messages/`
```json
{
  "senderId": "user123",
  "content": "Hello there!"
}
```

#### Get Chat Messages
**GET** `/chats/{chatId}/messages/`

## 📊 Database Schema

### Users Table
- `userId` (PK, String)
- `name` (String)
- `gender` (String)
- `age` (Integer)
- `bio` (Text)
- `email` (String, Unique)
- `profilePhoto` (URL)
- `latitude`, `longitude` (Decimal)
- `activePincodes` (JSON Array)
- `followers`, `following` (JSON Arrays)
- `idCardUrl` (URL)

### Follow Requests
- `documentId` (PK, Auto)
- `fromUserId` (String)
- `toUserId` (String)
- `status` (pending/accepted/rejected)
- `createdAt` (Timestamp)

### Followers
- `documentId` (PK, Auto)
- `followerId` (String)
- `followingId` (String)
- `createdAt` (Timestamp)

### Posts
- `postId` (PK, Auto)
- `userId` (String)
- `description` (Text)
- `mediaType` (image/video)
- `mediaURL` (URL)
- `pincode` (String)
- `location` (JSON)
- `timestamp` (Timestamp)

### Stories
- `storyId` (PK, Auto)
- `userId` (String)
- `description` (Text)
- `mediaType` (image/video)
- `mediaURL` (URL)
- `expireAt` (Timestamp)
- `createdAt` (Timestamp)

### Chats
- `chatId` (PK, Auto)
- `users` (JSON Array)
- `lastMessage` (Text)
- `lastMessageTime` (Timestamp)

### Messages
- `messageId` (PK, Auto)
- `chatId` (Integer, FK)
- `senderId` (String)
- `content` (Text)
- `timestamp` (Timestamp)

## 🧪 Testing

Run the comprehensive test suite:
```bash
python test_all_apis.py
```

This tests all 13 endpoints and verifies:
- User CRUD operations
- Follow/unfollow flow
- Post creation and retrieval
- Story creation
- Chat and messaging

## ✅ Connection Status

- ✅ Successfully connected to Supabase PostgreSQL (Session Pooler)
- ✅ Database: `postgres`
- ✅ Host: `aws-1-ap-southeast-1.pooler.supabase.com:5432`
- ✅ All migrations applied
- ✅ All endpoints tested and working

## 🛠 Technology Stack

- **Framework**: Django 5.0
- **API**: Django REST Framework
- **Database**: Supabase PostgreSQL
- **Database Client**: psycopg2-binary
- **CORS**: django-cors-headers
- **Environment**: python-dotenv

## 📝 Notes

1. The API uses Session Pooler connection mode for Supabase Free tier compatibility
2. All timestamps are in UTC
3. Stories automatically expire based on `expireAt` timestamp
4. Follow relationships are bidirectional and maintain both follower/following arrays
5. Chats automatically update `lastMessage` and `lastMessageTime` when messages are sent

## 🎯 All Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/users/` | POST | Create user profile |
| `/users/` | GET | Get all users |
| `/users/{userId}/` | GET | Get user by ID |
| `/users/{userId}/` | PATCH | Update user |
| `/users/{userId}/follow/` | POST | Send follow request |
| `/users/{userId}/accept-follow/` | POST | Accept/reject follow |
| `/users/{userId}/followers/` | GET | Get followers |
| `/users/{userId}/following/` | GET | Get following |
| `/users/{userId}/unfollow/` | POST | Unfollow user |
| `/posts/` | POST | Create post |
| `/users/{userId}/posts/` | GET | Get user's posts |
| `/stories/` | POST | Create story |
| `/users/{userId}/stories/` | GET | Get user's active stories |
| `/chats/get-or-create/` | POST | Get or create chat |
| `/chats/{chatId}/messages/` | POST | Send message |
| `/chats/{chatId}/messages/` | GET | Get chat messages |

**Server running at:** http://127.0.0.1:8000/

**All endpoints are working and tested! ✨**
# Social_Media_Platform_Backend
