import re
from app.db.supabase_client import get_supabase_client

class BaseService:
    """
    Base service class for all authenticated Supabase-backed services.

    This class is responsible for:
    - Assigning attributes for use by other services from the AuthService
    - Providing helper functions multiple services might use

    Attributes:
        supabase (Client):
            An authenticated Supabase client instance.

        access_token (str):
            The authenticated user's access token

        refresh_token (str):
            The authenticated user's refresh token


    Methods:
        __init__(email: str, password: str):
            Signs in a user using the provided credentials and assigns the
            attributes outlined above.

        verify_query(query: query) -> APIResponse:
            Verifies a query by ensuring it is executed without issue and
            actually returns data. 
            Returns the APIResponse.

        get_my_league() -> str:
            Returns the user's league UUID.

        get_my_team() -> str:
            Returns the user's team UUID.
    """
    def __init__(self, supabase, user_id, access_token, refresh_token):
        self.supabase = supabase
        self.user_id = user_id
        self.access_token = access_token
        self.refresh_token = refresh_token

        self.supabase.auth.set_session(access_token, refresh_token)
        
    def verify_query(self, query):
        try:
            result = query.execute()
        except Exception as e:
            raise Exception(f"Query execution failed: {e}")

        if result.data is None:
            return None

        return result
    
    def get_my_username(self):
        result = self.verify_query((
            self.supabase
            .table("managers")
            .select("manager_name")
            .eq("user_id", self.user_id)
            ))
        
        return result.data[0]["manager_name"]

    def get_my_league(self):
        result = self.verify_query((
            self.supabase
            .table("managers")
            .select("league_id")
            .eq("user_id", self.user_id)
            ))

        return result.data[0]["league_id"]

    def get_my_team(self):
        result = self.verify_query((
            self.supabase
            .table("teams")
            .select("team_id")
            .eq("team_owner", self.user_id)
            ))

        return result.data[0]["team_id"]