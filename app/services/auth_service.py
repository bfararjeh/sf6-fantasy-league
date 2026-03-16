import json
import os
from pathlib import Path

from app.db.supabase_client import get_supabase_client
from app.services.base_service import BaseService

class AuthService:
    '''
    Service responsible for authenticating user sessions.

    This service will authenticate a user and return a "BaseService" object.
    This base service object can then be used to instantiate other services.
    
    Methods:
    login(email: str, password: str) -> BaseService
        Logs in a user with an email and password and then returns an 
        authenticated "BaseService" object.
    
    login_with_token(token_data: dict) -> BaseService
        Logs in a user using their cached access token and refresh token, saved
        into AppData.Roaming.FantasySF6 on login, before returning a
        authenticated "BaseService" object
    '''
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

    @staticmethod
    def login_with_token(token_data: dict) -> BaseService:
        refresh_token = token_data.get("refresh_token")
        if not refresh_token:
            raise ValueError("Missing refresh token for session restoration")

        supabase = get_supabase_client()

        try:
            auth_response = supabase.auth.refresh_session(refresh_token)
            session = auth_response.session

            return BaseService(
                supabase=supabase,
                user_id=session.user.id,
                access_token=session.access_token,
                refresh_token=session.refresh_token
            )

        except Exception as e:
            raise Exception(f"Failed to restore session: {e}")


class AuthStore:
    '''
    Methods for saving, loading, and clearing stored sessions. Nothing fancy,
    just json dumps and path grabbing using the os library.

    Method names are self explanatory.
    '''
    _filename = "session.json"

    @classmethod
    def _path(cls) -> Path:
        if os.name == "nt":
            base = Path(os.environ["APPDATA"]) / "FantasySF6"
        base.mkdir(parents=True, exist_ok=True)
        return base / cls._filename

    @classmethod
    def save(cls, auth_data: dict):
        with open(cls._path(), "w", encoding="utf-8") as f:
            json.dump(auth_data, f)

    @classmethod
    def load(cls) -> dict | None:
        path = cls._path()
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def clear(cls):
        path = cls._path()
        if path.exists():
            path.unlink()
