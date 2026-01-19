import re
from app.db.supabase_client import get_supabase_client

class SignupService():
    """
    Handles user creation. Interacts with Supabase Auth and the 'managers' 
    table by inserting new rows for each new user.

    Methods:
    __init__(email: str, password: str, manager_name: str)
        Create a new user and corresponding manager row. Also verifies password 
        is of correct length and manager name is valid (length, chars).
    """
    def __init__(self):
        self.supabase = get_supabase_client()

    def signup(self, email: str, password: str, manager_name: str):

        # pass & username validation
        if len(password) < 8:
            raise Exception("Password must be at least 8 characters long.")
        if 2 > len(manager_name) or len(manager_name) > 16:
            raise Exception("Username must be inbetween 2 and 16 characters.")
        if not re.fullmatch(r"^[\w']+$", manager_name):
            raise Exception("Username must only include letters, numbers, underscores, and apostrophes.")

        # sign up the user
        try:
            response = self.supabase.auth.sign_up({"email": email, "password": password})
            auth_id = response.user.id
        except Exception as e:
            raise Exception(f"Signup failed: {e}")

        # insert user to database
        # if this fails, the user will become orphaned - ggs
        (self.supabase
        .table("managers")
        .insert({
            "user_id": auth_id,
            "manager_name": manager_name
            })
        .execute()
        )

        return True