import os
from supabase import create_client

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

def get_admin_client():
    """
    Returns an admin Supabase client using the secret key.
    Secret key stays in .env of course.
    """
    if not SUPABASE_URL:
        raise ValueError("SUPABASE_URL not set")

    if not SUPABASE_SECRET_KEY:
        raise ValueError("SUPABASE_SECRET_KEY not set")
    
    client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    return client