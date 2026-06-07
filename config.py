import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    # Supabase configurations
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    
    # Secret Key for Flask sessions cookie encryption
    SECRET_KEY = os.environ.get("SECRET_KEY", "store-data-collection-session-secret-key-12345")
    
    # Admin Credentials
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin") # Super Admin (Bharath Kumar)
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@123")
    
    SADDAM_USERNAME = os.environ.get("SADDAM_USERNAME", "saddam") # Admin & Store Head (Saddam Husain)
    SADDAM_PASSWORD = os.environ.get("SADDAM_PASSWORD", "Saddam@123")
    
    @classmethod
    def check_config(cls):
        missing = []
        if not cls.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not cls.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        return missing
