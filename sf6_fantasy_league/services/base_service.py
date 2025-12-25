from sf6_fantasy_league.db.supabase_client import get_supabase_client

class BaseService:
    """
    Base service class for all authenticated Supabase-backed services.

    This class is responsible for:
    - Initializing an authenticated Supabase client using a user's access token
    - Verifying that the client session is properly authenticated
    - Storing the authenticated user's `user_id` for downstream queries
    - Providing common helper methods for accessing manager (user) data

    Attributes:
        user_id (str):
            The authenticated user's UUID, used as the primary key in the
            `managers` table.

        supabase (Client):
            An authenticated Supabase client instance scoped to the user
            session via the provided access token.

        auth_id (str):
            The authenticated Supabase auth user ID, as returned by
            `supabase.auth.get_user()`.

    Methods:
        get_my_user():
            Returns the current user's manager row from the `managers` table.

        get_all_user():
            Returns all manager rows from the `managers` table.
    """
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
    
    def verify_query(self, query):
        try:
            result = query.execute()
        except Exception as e:
            raise Exception(f"Query execution failed: {e}")

        if result.data is None:
            raise Exception("Query ran successfully but returned no data.")

        return result

    def get_my_user(self):
        result = self.verify_query((
            self.supabase
            .table("managers")
            .select("*")
            .eq("user_id", self.user_id)
            ))

        return result.data[0]
    
    def get_my_league(self):
        result = self.verify_query((
            self.supabase
            .table("managers")
            .select("league_id")
            .eq("user_id", self.user_id)
            ))

        return result.data[0]

    def get_all_user(self):
        result = self.verify_query((
            self.supabase
            .table("managers")
            .select("*")
            ))
        
        return result.data