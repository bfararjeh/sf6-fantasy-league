from supabase import create_client

SUPABASE_URL = "https://idnmrntzyljrppeocbpa.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_oLJyY3yFFqYoXP3-xvzTWA_aS6dGneP"

def get_supabase_client():
    """
    Returns a Supabase client using the anon key.

    Note: The client is unauthenticated by default. Services that need 
    authenticated access must call `auth.set_session(access_token)` 
    after retrieving the client.
    """
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return client