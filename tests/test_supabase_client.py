import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SubaseUrl', 'https://khudodonuubcqupqskxr.supabase.co')
SUPABASE_ANON_KEY = os.getenv('ANON_PUBLIC')
SUPABASE_SERVICE_ROLE = os.getenv('SERVICE_ROLE')

print("🔍 Testing Supabase Client Connection")
print(f"URL: {SUPABASE_URL}")
print(f"Anon Key: {SUPABASE_ANON_KEY[:20]}...")
print(f"Service Role: {SUPABASE_SERVICE_ROLE[:20]}...")

# Test with anon key
try:
    print("\n🧪 Testing with Anon Key...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    # Try to fetch from a table (this should work if connection is good)
    response = supabase.table('users').select('*').limit(1).execute()
    print("✅ Anon Key Connection: SUCCESS")
    print(f"Response: {response}")

except Exception as e:
    print(f"❌ Anon Key Connection: FAILED - {str(e)}")

# Test with service role key
try:
    print("\n🧪 Testing with Service Role Key...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)

    # Try to fetch from a table
    response = supabase.table('users').select('*').limit(1).execute()
    print("✅ Service Role Connection: SUCCESS")
    print(f"Response: {response}")

except Exception as e:
    print(f"❌ Service Role Connection: FAILED - {str(e)}")

# Test database connection directly
try:
    print("\n🧪 Testing Database Direct Connection...")
    # Try to create a table or check if tables exist
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)

    # Check if we can list tables or get schema info
    # This is a basic connectivity test
    response = supabase.rpc('version').execute()
    print("✅ Database Direct Connection: SUCCESS")
    print(f"Version: {response}")

except Exception as e:
    print(f"❌ Database Direct Connection: FAILED - {str(e)}")

print("\n📋 TROUBLESHOOTING SUMMARY:")
print("1. If all connections fail: Check your Supabase project URL and keys")
print("2. If anon key fails but service role works: Check RLS policies")
print("3. If service role fails: Check database connectivity and credentials")
print("4. Check Supabase dashboard for any error messages or maintenance notices")