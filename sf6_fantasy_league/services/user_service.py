from sf6_fantasy_league.db.supabase_client import get_supabase_client
import re

class UserService:
    """
    Handles user authentication and account management (i.e. signing up and 
    logging in)

    Interacts with Supabase Auth and the 'managers' table by inserting new rows
    for each new user.

    Methods
    -------
    signup(email: str, password: str, manager_name: str) -> str
        Create a new user and corresponding manager row. Also verifies password 
        is of correct length and manager name is valid (length, chars).
        Returns the user ID.
        
    login(email: str, password: str) -> dict
        Log in an existing user. Returns a dict with user_id and access_token.
    """
    def __init__(self):
        self.supabase = get_supabase_client()
        self.current_user = None
        self.access_token = None

    def signup(self, email, password, manager_name):
        # pass & username validation
        if len(password) < 8:
            raise Exception("Password must be at least 8 characters long.")
        if 4 > len(manager_name) or len(manager_name) > 16:
            raise Exception("Username must be inbetween 4 and 16 characters.")
        if not re.fullmatch(r'^\w+$', manager_name):
            raise Exception("Username must only include letters, numbers, and underscores.")

        # sign up the user
        try:
            response = self.supabase.auth.sign_up({"email": email, "password": password})
            user = getattr(response, "user", None) or response.data
        except Exception as e:
            raise Exception(f"Signup failed: {e}")

        if not user:
            raise Exception(f"Signup failed: {response.data}")

        # insert the manager row into the db
        self.current_user = user
        insert_data = {
            "user_id": user.id,
            "manager_name": manager_name,
        }
        self.supabase.table("managers").insert(insert_data).execute()
        return user.id

    def login(self, email, password):
        if not email or not password:
            raise ValueError("Email and password must be provided")

        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            session = getattr(response, "session", None) or response.data
        except Exception as e:
            raise Exception(f"Login failed: {e}")

        if not session:
            raise Exception(f"Login failed: {response.data}")

        # verify user exists in managers table
        user_id = session.user.id
        manager_check = self.supabase.table("managers").select("*").eq("user_id", user_id).execute()
        if not manager_check.data:
            raise Exception("Login failed: User not found.")

        self.current_user = session.user
        self.access_token = getattr(session, "access_token", None)
        return {"user_id": self.current_user.id, "access_token": self.access_token}