from app.db.supabase_client import get_supabase_client
from app.services.base_service import BaseService


class AuthService:
    @staticmethod
    def login(email: str, password: str) -> BaseService:
        if not email or not password:
            raise ValueError("Email and password must be provided.")

        supabase = get_supabase_client()

        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        session = response.session

        return BaseService(
            supabase=supabase,
            user_id=response.user.id,
            access_token=session.access_token,
            refresh_token=session.refresh_token
        )