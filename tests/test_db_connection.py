#!/usr/bin/env python
"""
Test script to find correct Supabase connection settings
"""
import psycopg2
import os

# Test configurations
configs = [
    {
        "name": "Config 1: Direct connection port 5432",
        "host": "db.khudodonuubcqupqskxr.supabase.co",
        "port": 5432,
        "user": "postgres",
        "password": "YA56ec3QY4C5uz7W",
        "database": "postgres"
    },
    {
        "name": "Config 2: Pooler port 6543 with postgres.ref user",
        "host": "aws-0-ap-south-1.pooler.supabase.com",
        "port": 6543,
        "user": "postgres.khudodonuubcqupqskxr",
        "password": "YA56ec3QY4C5uz7W",
        "database": "postgres"
    },
    {
        "name": "Config 3: Pooler port 6543 with postgres user",
        "host": "aws-0-ap-south-1.pooler.supabase.com",
        "port": 6543,
        "user": "postgres",
        "password": "YA56ec3QY4C5uz7W",
        "database": "postgres"
    },
    {
        "name": "Config 4: Pooler port 5432",
        "host": "aws-0-ap-south-1.pooler.supabase.com",
        "port": 5432,
        "user": "postgres",
        "password": "YA56ec3QY4C5uz7W",
        "database": "postgres"
    },
]

for config in configs:
    print(f"\n{'='*60}")
    print(f"Testing: {config['name']}")
    print(f"{'='*60}")
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            connect_timeout=5
        )
        print("✅ CONNECTION SUCCESSFUL!")
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"PostgreSQL Version: {version[0][:50]}...")
        cursor.close()
        conn.close()
        print("\n🎉 USE THIS CONFIGURATION!")
        break
    except Exception as e:
        print(f"❌ FAILED: {str(e)[:100]}")

print(f"\n{'='*60}\n")
