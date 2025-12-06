#!/usr/bin/env python
"""
Django database connection test
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        row = cursor.fetchone()
        print("✅ Django database connection successful!")
        print(f"PostgreSQL version: {row[0][:80]}")
        
        # Test creating a simple table
        print("\nTesting table creation...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_connection (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100)
            );
        """)
        print("✅ Table creation successful!")
        
        # Clean up
        cursor.execute("DROP TABLE IF EXISTS test_connection;")
        print("✅ Cleanup successful!")
        
except Exception as e:
    print(f"❌ Django database connection failed: {e}")
    print(f"\nFull error: {str(e)}")
