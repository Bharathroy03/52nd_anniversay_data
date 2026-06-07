import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Supabase configurations
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    
    # Secret key for signing JWT tokens - fallback to a default secure-looking string if not set
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "store-data-collection-super-secret-key-change-this")
    
    # JWT Token Expiry in seconds (e.g., 2 hours)
    JWT_EXPIRY_SECONDS = int(os.environ.get("JWT_EXPIRY_SECONDS", 7200))
    
    # Admin Credentials
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@123")
    
    # Check if necessary configs are missing and issue warnings
    @classmethod
    def check_config(cls):
        missing = []
        if not cls.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not cls.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        return missing
