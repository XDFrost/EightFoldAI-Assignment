from supabase import create_async_client, AsyncClient
from app.Config.dataConfig import Config

settings = Config.Config.from_env()

async def get_supabase_client() -> AsyncClient:
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValueError("Supabase URL and Key must be set")
    return await create_async_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
