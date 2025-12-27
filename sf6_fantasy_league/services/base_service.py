import re
from sf6_fantasy_league.db.supabase_client import get_supabase_client

class BaseService:
    """
    Base service class for all authenticated Supabase-backed services.

    This class is responsible for:
    - Initialising an authenticated Supabase client by logging in a user
    - Assigning attributes for use by other services
    - Providing helper functions multiple services might use

    Attributes:
        supabase (Client):
            An authenticated Supabase client instance.

        user_id (str):
            The authenticated user's UUID, used as the primary key in the
            `managers` table.

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
            
        get_my_user() -> str:
            Returns the current user's manager row from the `managers` table.

        get_my_league() -> str:
            Returns the user's league UUID.
    """
    def __init__(self, email: str, password: str):
        if not email or not password:
            raise ValueError("Email and password must be provided.")

        self.supabase = get_supabase_client()

        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            session = response.session
        except Exception as e:
            raise Exception(f"Login failed: {e}")

        # init tokens and user id
        self.user_id = response.user.id
        self.access_token = session.access_token
        self.refresh_token = session.refresh_token
        self.supabase.auth.set_session(session.access_token, session.refresh_token)

        self.verify_query(
            self.supabase
            .table("managers")
            .select("*")
            .eq("user_id", self.user_id)
        )

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

        return result.data[0]["league_id"]
