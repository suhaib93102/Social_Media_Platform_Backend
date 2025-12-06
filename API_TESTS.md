# API Testing Guide

This document contains quick and well-organized API testing instructions and example curl commands for frontend developers to quickly test the Social Media Platform backend.

Base URL
--------
- Deployed URL: `https://social-media-platform-backend-4oz4.onrender.com`

Notes
-----
- No external authentication is required for these endpoints; `userId` is used for identification in this app.
- All endpoints accept and return JSON.
- Use the sample requests below for integration and smoke testing. If you need a Postman collection, I can export one separately.

General curl options used in the examples:
- -s: Silent mode for compact output
- -H "Content-Type: application/json": For JSON request bodies

Users
-----
1. Create User (Signup)

```bash
curl -s -X POST "https://social-media-platform-backend-4oz4.onrender.com/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "frontend001",
    "name": "Frontend Dev",
    "gender": "other",
    "age": 26,
    "bio": "Testing the API",
    "email": "frontend001@example.com",
    "profilePhoto": "https://example.com/photo.jpg",
    "latitude": 12.9716,
    "longitude": 77.5946
  }'
```

2. Get All Users

```bash
curl -s -X GET "https://social-media-platform-backend-4oz4.onrender.com/users/"
```

3. Get User by ID (Login-style retrieval)

```bash
curl -s -X GET "https://social-media-platform-backend-4oz4.onrender.com/users/frontend001/"
```

4. Update User (PATCH)

```bash
curl -s -X PATCH "https://social-media-platform-backend-4oz4.onrender.com/users/frontend001/" \
  -H "Content-Type: application/json" \
  -d '{"bio": "Updated from frontend test", "age": 27}'
```

Follow and Unfollow
-------------------
1. Send Follow Request

```bash
curl -s -X POST "https://social-media-platform-backend-4oz4.onrender.com/users/frontend001/follow/" \
  -H "Content-Type: application/json" \
  -d '{"toUserId": "someOtherUser"}'
```

2. Accept Follow Request

```bash
curl -s -X POST "https://social-media-platform-backend-4oz4.onrender.com/users/someOtherUser/accept-follow/" \
  -H "Content-Type: application/json" \
  -d '{"fromUserId": "frontend001", "status": "accepted"}'
```

3. Get Followers

```bash
curl -s -X GET "https://social-media-platform-backend-4oz4.onrender.com/users/someOtherUser/followers/"
```

4. Get Following

```bash
curl -s -X GET "https://social-media-platform-backend-4oz4.onrender.com/users/frontend001/following/"
```

Posts & Stories
---------------
1. Create Post

```bash
curl -s -X POST "https://social-media-platform-backend-4oz4.onrender.com/posts/" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "frontend001",
    "description": "Hello from frontend!",
    "mediaType": "image",
    "mediaURL": "https://example.com/image.jpg",
    "pincode": "560001",
    "location": {"latitude": 12.9716, "longitude": 77.5946, "address": "Bengaluru"}
  }'
```

2. Get Posts by a User

```bash
curl -s -X GET "https://social-media-platform-backend-4oz4.onrender.com/users/frontend001/posts/"
```

3. Create Story

```bash
curl -s -X POST "https://social-media-platform-backend-4oz4.onrender.com/stories/" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "frontend001",
    "description": "Story from frontend",
    "mediaType": "image",
    "mediaURL": "https://example.com/story.jpg",
    "expireAt": "2025-12-07T12:00:00Z"
  }'
```

Chats & Messages
----------------
1. Create/Get Chat

```bash
curl -s -X POST "https://social-media-platform-backend-4oz4.onrender.com/chats/get-or-create/" \
  -H "Content-Type: application/json" \
  -d '{"user1": "frontend001", "user2": "someOtherUser"}'
```

Response returns a `chatId` which can be used for messages.

2. Send Message

```bash
curl -s -X POST "https://social-media-platform-backend-4oz4.onrender.com/chats/<CHAT_ID>/messages/" \
  -H "Content-Type: application/json" \
  -d '{"senderId": "frontend001", "content": "Hello!"}'
```

3. Get Messages in Chat

```bash
curl -s -X GET "https://social-media-platform-backend-4oz4.onrender.com/chats/<CHAT_ID>/messages/"
```

Quick Smoke Test Script (Authentication-only)
-----------------------
A small script `smoke_test.sh` is present in the repo that runs quick authentication-related checks (signup, login, invalid login, duplicate signup).

Run it with the default BASE_URL:

```bash
chmod +x smoke_test.sh
./smoke_test.sh
```

To run against a different environment, set `BASE_URL` and/or `USER_ID` and `USER_EMAIL` on the command line:

```bash
BASE_URL=https://local.example:8000 USER_ID=testuser USER_EMAIL=testuser@example.com ./smoke_test.sh
```

Python Test Scripts
-------------------
- Use `test_auth.py` for detailed login/signup tests (suitable for CI or local checks).
- Use `test_all_apis.py` for a full test of the entire API behavior (bulk smoke test for all endpoints).

Support & Notes
----------------
- If you need Postman or Insomnia collections, or a file with JSON payloads for each endpoint, I can also add that.
- If any endpoint returns unexpected results, please capture the request and response payloads and open an issue or message for a fix.

---

If you'd like, I can also generate and add a `postman_collection.json` for convenient import; just confirm and I’ll produce it.