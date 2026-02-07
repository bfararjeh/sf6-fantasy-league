import io
import uuid
from PIL import Image
import requests


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

    def assign_avatar(self, image):
        """
        Processes and uploads a user's avatar.
        """

        MAX_OUTPUT_BYTES = 200 * 1024
        BUCKET = "avatars"

        # load image, convert to rgb check aspect ratio 
        try:
            img = Image.open(image)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            width, height = img.size
            ratio = width / height

            if abs(ratio - 1.0) > 0.01:
                raise Exception("Avatar must be square (1:1 aspect ratio).")

        except Exception as e:
            raise Exception(f"Invalid image file: {e}")


        # compress image
        try:
            buffer = io.BytesIO()
            quality = 90

            while quality >= 40:
                buffer.seek(0)
                buffer.truncate()

                img.save(
                    buffer,
                    format="WEBP",
                    quality=quality,
                    method=6
                )

                if buffer.tell() <= MAX_OUTPUT_BYTES:
                    break

                quality -= 5

            if buffer.tell() > MAX_OUTPUT_BYTES:
                raise Exception("Could not compress avatar under 200KB")

            buffer.seek(0)

        except Exception as e:
            raise Exception(f"Could not compress avatar: {e}")

        # upload
        try:
            file_name = f"{self.user_id}.webp"
            self.supabase.storage.from_(BUCKET).upload(
                file_name,
                buffer.getvalue(),
                file_options={
                    "content-type": "image/webp",
                    "upsert": "true"
                }
            )
        except Exception as e:
            raise Exception(f"Avatar upload failed: {e}")

    def get_avatar(self, user_id):
        """
        Retrieves a user's avatar as an object to be put into a QPixmap
        """

        BUCKET = "avatars"

        # make sure user id is valid uuid
        try:
            uuid.UUID(str(user_id))
        except ValueError as e:
            raise Exception(f"User ID is not a valid UUID: {e}")

        try:
            avatar_path = str(user_id) + ".webp"

            # get url
            avatar_url = self.supabase.storage.from_(BUCKET).get_public_url(avatar_path)

            if not avatar_url:
                return None

            # fetch image bytes
            response = requests.get(avatar_url)
            response.raise_for_status()  # raise error if download failed
            return response.content

        except Exception as e:
            raise Exception (f"Failed to get avatar for user {user_id}: {e}")

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
            .select("blocking, warning_message, banner_message, version")
            .order("updated_at", desc=True)
            .limit(1)
        ))

        return result.data[0] if result.data else None