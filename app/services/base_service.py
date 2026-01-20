
class BaseService:
    """
    Base service class for all authenticated Supabase-backed services.

    This class is responsible for assigning base attributes and methods for
    use by other services.

    Attributes:
        supabase (Client):
            An authenticated Supabase client instance
        
        user_id (str):
            An authenticated users UUID

        access_token (str):
            The authenticated user's access token

        refresh_token (str):
            The authenticated user's refresh token


    Methods:
        __init__(supabase: Client, user_id: str, access_token: str, refresh_token: str):
            Sets all the class attributes.

        verify_query(query: query) -> APIResponse:
            Verifies a query by ensuring it is executed without issue and
            actually returns data. Returns the APIResponse or None if the 
            query returned empty.

        get_my_username() -> str:
            Returns the user's username

        get_my_league() -> str:
            Returns the user's league UUID

        get_my_league() -> str:
            Returns the user's league UUID

        get_system_state() -> dict:
            Returns the newest system message
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
        
        if not result.data:
            return None

        return result.data[0]["league_id"]

    def get_my_team(self):
        result = self.verify_query((
            self.supabase
            .table("teams")
            .select("team_id")
            .eq("team_owner", self.user_id)
            ))
        
        if not result.data:
            return None

        return result.data[0]["team_id"]

    def get_system_state(self):
        result = self.verify_query((
            self.supabase
            .table("system_state")
            .select("blocking, warning_message, banner_message, last_live_scores")
            .order("updated_at", desc=True)
            .limit(1)
        ))

        return result.data[0] if result.data else None