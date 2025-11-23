import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.supabase_client import get_supabase_client
from app.Config.dataConfig import Config

settings = Config.Config.from_env()
import json

import asyncio

async def verify():
    print("Connecting to Supabase...")
    supabase = await get_supabase_client()
    
    try:
        print("Fetching latest account plan...")
        # Fetch the most recently created plan
        response = await supabase.table("account_plans").select("*").order("created_at", desc=True).limit(1).execute()
        
        data = response.data
        if data and len(data) > 0:
            plan = data[0]
            print("\n✅ SUCCESS: Found a plan in the database!")
            print(f"ID: {plan['id']}")
            print(f"Company: {plan['company']}")
            print(f"Created At: {plan['created_at']}")
            print(f"Sections: {list(plan.get('sections', {}).keys())}")
        else:
            print("\n❌ NO DATA: The 'account_plans' table is empty.")
            
    except Exception as e:
        print(f"\n❌ ERROR: Failed to fetch data: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
