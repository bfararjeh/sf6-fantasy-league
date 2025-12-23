from sf6_fantasy_league.db.supabase_client import get_supabase_client

class BaseService:
    def __init__(self, access_token: str, user_id: str):
        if not access_token or not user_id:
            raise ValueError("Access token and user_id required")

        self.user_id = user_id
        self.supabase = get_supabase_client()

        # attach access token to session
        self.supabase.auth.set_session(access_token, refresh_token="dummy_refresh_token")

        # get authenticated user
        user_response = self.supabase.auth.get_user()
        if user_response is None or user_response.user is None:
            raise Exception("Client is not authenticated.")
        self.auth_id = user_response.user.id