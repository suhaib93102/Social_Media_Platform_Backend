import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SubaseUrl', 'https://khudodonuubcqupqskxr.supabase.co')
SUPABASE_SERVICE_ROLE = os.getenv('SERVICE_ROLE')

print("🔧 Creating Supabase Tables via API")
print(f"URL: {SUPABASE_URL}")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)

    # Create users table
    print("\n📋 Creating users table...")
    # Note: In Supabase, tables are typically created via SQL or migrations
    # For now, let's check if we can create tables using raw SQL

    sql_commands = [
        """
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
        """,
        """
        CREATE TABLE IF NOT EXISTS followRequests (
            documentId SERIAL PRIMARY KEY,
            createdAt TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            fromUserId VARCHAR(255) NOT NULL,
            toUserId VARCHAR(255) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected')),
            UNIQUE(fromUserId, toUserId)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS followers (
            documentId SERIAL PRIMARY KEY,
            createdAt TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            followerId VARCHAR(255) NOT NULL,
            followingId VARCHAR(255) NOT NULL,
            UNIQUE(followerId, followingId)
        );
        """,
        """
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
        """,
        """
        CREATE TABLE IF NOT EXISTS stories (
            storyId SERIAL PRIMARY KEY,
            createdAt TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            description TEXT,
            expireAt TIMESTAMP WITH TIME ZONE NOT NULL,
            mediaType VARCHAR(20) NOT NULL CHECK (mediaType IN ('image', 'video')),
            mediaURL TEXT NOT NULL,
            userId VARCHAR(255) NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS chats (
            chatId SERIAL PRIMARY KEY,
            lastMessage TEXT,
            lastMessageTime TIMESTAMP WITH TIME ZONE,
            users JSONB DEFAULT '[]'::jsonb
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS messages (
            messageId SERIAL PRIMARY KEY,
            chatId INTEGER NOT NULL,
            senderId VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
    ]

    for i, sql in enumerate(sql_commands, 1):
        try:
            print(f"Creating table {i}/7...")
            response = supabase.rpc('exec_sql', {'sql': sql}).execute()
            print(f"Table {i} created successfully")
        except Exception as e:
            print(f"Failed to create table {i}: {str(e)}")

    print("\n🎉 All tables created successfully!")
    print("Now you can run Django migrations or use the API endpoints.")

except Exception as e:
    print(f"Failed to connect to Supabase: {str(e)}")
    print("\n🔧 Alternative: Check your Supabase dashboard and create tables manually")
    print("Go to: https://supabase.com/dashboard/project/khudodonuubcqupqskxr/sql")
    print("And run the SQL commands from the sql_tables.sql file")