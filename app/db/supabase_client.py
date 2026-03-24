from supabase import create_client

SUPABASE_URL = "https://idnmrntzyljrppeocbpa.supabase.co/"
SUPABASE_ANON_KEY = "sb_publishable_oLJyY3yFFqYoXP3-xvzTWA_aS6dGneP"

def get_supabase_client():
    """
    Returns an unauthenticated Supabase client using the anon key.
    This is the only place in the entire project wherethe Supabase anon key is
    present.
    """
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return client