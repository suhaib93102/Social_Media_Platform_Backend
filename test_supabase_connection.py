import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase connection details
SUPABASE_DB_PASSWORD = os.getenv('SUPABASE_DB_PASSWORD', 'LaxCcFXYf4OAy9zG')

# Try different connection configurations
configs = [
    {
        "name": "Session Pooler (Port 5432)",
        "host": "aws-0-ap-south-1.pooler.supabase.com",
        "port": "5432",
        "user": "postgres.khudodonuubcqupqskxr",
        "password": SUPABASE_DB_PASSWORD,
        "database": "postgres"
    },
    {
        "name": "Transaction Pooler (Port 6543)",
        "host": "aws-0-ap-south-1.pooler.supabase.com",
        "port": "6543",
        "user": "postgres.khudodonuubcqupqskxr",
        "password": SUPABASE_DB_PASSWORD,
        "database": "postgres"
    },
    {
        "name": "Direct Connection (Port 5432)",
        "host": "db.khudodonuubcqupqskxr.supabase.co",
        "port": "5432",
        "user": "postgres",
        "password": SUPABASE_DB_PASSWORD,
        "database": "postgres"
    },
    {
        "name": "Alternative Direct Connection",
        "host": "khudodonuubcqupqskxr.supabase.co",
        "port": "5432",
        "user": "postgres",
        "password": SUPABASE_DB_PASSWORD,
        "database": "postgres"
    }
]

for config in configs:
    try:
        print(f"\nTrying {config['name']}:")
        print(f"Host: {config['host']}:{config['port']}")
        print(f"User: {config['user']}")

        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            connect_timeout=10
        )

        # Test the connection
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ SUCCESS: Connected to {config['name']}")
        print(f"PostgreSQL version: {version[0][:50]}...")

        cursor.close()
        conn.close()
        break

    except Exception as e:
        print(f"❌ FAILED: {config['name']} - {str(e)}")

else:
    print("\n❌ All connection attempts failed!")
    print("\n🔧 TROUBLESHOOTING STEPS:")
    print("1. Check your Supabase dashboard: https://supabase.com/dashboard/project/khudodonuubcqupqskxr/settings/database")
    print("2. Verify the password is correct: YA56ec3QY4C5uz7W")
    print("3. Check if there's an IP allowlist in Database > Settings > Allowlist")
    print("4. Make sure your project reference ID is correct: khudodonuubcqupqskxr")
    print("5. Try resetting your database password in Supabase if needed")