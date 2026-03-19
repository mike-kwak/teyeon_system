import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY") # service_role key is better if available, but let's try anon

supabase: Client = create_client(url, key)

# Since we don't have a direct raw SQL execution through the standard python client,
# and psql failed, we can't easily run ALTER TABLE from here if RLS/Permissions block it via REST.
# However, usually users can run this in Supabase SQL Editor.
# We will just assume the column is there for the code, but I'll try to check if it exists.

try:
    # Try fetching one member to see if birthdate exists
    res = supabase.table("members").select("birthdate").limit(1).execute()
    print("Column 'birthdate' already exists.")
except Exception as e:
    print(f"Error or column missing: {e}")
    print("Please run 'ALTER TABLE members ADD COLUMN birthdate DATE;' in Supabase SQL Editor.")
