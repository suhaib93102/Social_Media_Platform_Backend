-- Social App Database Tables for Supabase
-- Run this in your Supabase SQL Editor: https://supabase.com/dashboard/project/khudodonuubcqupqskxr/sql

-- Users table
CREATE TABLE IF NOT EXISTS users (
    userId VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    gender VARCHAR(50),
    age INTEGER,
    bio TEXT,
    email VARCHAR(255) UNIQUE NOT NULL,
    profilePhoto TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    updatedAt TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    activePincodes JSONB DEFAULT '[]'::jsonb,
    followers JSONB DEFAULT '[]'::jsonb,
    following JSONB DEFAULT '[]'::jsonb,
    idCardUrl TEXT
);

-- Follow Requests table
CREATE TABLE IF NOT EXISTS followRequests (
    documentId SERIAL PRIMARY KEY,
    createdAt TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fromUserId VARCHAR(255) NOT NULL,
    toUserId VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected')),
    UNIQUE(fromUserId, toUserId)
);

-- Followers table
CREATE TABLE IF NOT EXISTS followers (
    documentId SERIAL PRIMARY KEY,
    createdAt TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    followerId VARCHAR(255) NOT NULL,
    followingId VARCHAR(255) NOT NULL,
    UNIQUE(followerId, followingId)
);

-- Posts table
CREATE TABLE IF NOT EXISTS posts (
    postId SERIAL PRIMARY KEY,
    description TEXT,
    mediaType VARCHAR(20) NOT NULL CHECK (mediaType IN ('image', 'video')),
    mediaURL TEXT NOT NULL,
    pincode VARCHAR(10),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    userId VARCHAR(255) NOT NULL,
    location JSONB DEFAULT '{}'::jsonb
);

-- Stories table
CREATE TABLE IF NOT EXISTS stories (
    storyId SERIAL PRIMARY KEY,
    createdAt TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT,
    expireAt TIMESTAMP WITH TIME ZONE NOT NULL,
    mediaType VARCHAR(20) NOT NULL CHECK (mediaType IN ('image', 'video')),
    mediaURL TEXT NOT NULL,
    userId VARCHAR(255) NOT NULL
);

-- Chats table
CREATE TABLE IF NOT EXISTS chats (
    chatId SERIAL PRIMARY KEY,
    lastMessage TEXT,
    lastMessageTime TIMESTAMP WITH TIME ZONE,
    users JSONB DEFAULT '[]'::jsonb
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    messageId SERIAL PRIMARY KEY,
    chatId INTEGER NOT NULL,
    senderId VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_posts_userId ON posts(userId);
CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON posts(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_stories_userId ON stories(userId);
CREATE INDEX IF NOT EXISTS idx_stories_expireAt ON stories(expireAt);
CREATE INDEX IF NOT EXISTS idx_messages_chatId ON messages(chatId);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);

-- Enable Row Level Security (RLS) if needed
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE stories ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE chats ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

COMMIT;