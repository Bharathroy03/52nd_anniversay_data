from supabase import create_client, Client
from config import Config

_supabase_client: Client = None

def get_supabase() -> Client:
    """
    Lazy-loads and returns the Supabase client.
    Raises RuntimeError if the environment variables are not configured.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
        
    url = Config.SUPABASE_URL
    key = Config.SUPABASE_KEY
    
    if not url or not key:
        raise RuntimeError(
            "Supabase credentials are missing. Please verify that "
            "SUPABASE_URL and SUPABASE_KEY are defined in the root .env file."
        )
        
    try:
        # Create and cache client
        _supabase_client = create_client(url, key)
        return _supabase_client
    except Exception as e:
        print(f"[ERROR] Failed to initialize Supabase client: {e}")
        raise RuntimeError(f"Could not connect to Supabase: {e}")
