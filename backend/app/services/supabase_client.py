from supabase import create_client, Client
from app.core.config import get_settings

settings = get_settings()

def get_supabase() -> Client:
    try:
        url = settings.SUPABASE_URL
        key = settings.SUPABASE_SECRET_KEY
        return create_client(url, key)
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
        # Return dummy or raise based on strictness
        raise e
