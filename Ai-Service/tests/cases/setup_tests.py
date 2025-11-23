import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.supabase_client import get_supabase_client

TEST_USER_ID = "00000000-0000-0000-0000-000000000000"

async def setup_test_user():
    print("Setting up test user...")
    supabase = await get_supabase_client()
    
    user_data = {
        "id": TEST_USER_ID,
        "email": "test@example.com",
        "password_hash": "hashed_secret", # Dummy hash
        "role": "user"
    }
    
    try:
        # Upsert the test user
        await supabase.table("users").upsert(user_data).execute()
        print(f"✅ SUCCESS: Test user {TEST_USER_ID} upserted.")
    except Exception as e:
        print(f"❌ ERROR: Failed to upsert test user: {e}")

if __name__ == "__main__":
    asyncio.run(setup_test_user())
