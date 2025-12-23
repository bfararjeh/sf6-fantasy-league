from sf6_fantasy_league.db.supabase_client import get_supabase_client
from sf6_fantasy_league.services.base_service import BaseService

class ManagerService(BaseService):
    """
    Service for accessing manager-related data for the authenticated user.

    This class provides methods to retrieve the logged-in user's manager row 
    and to fetch all managers in the same league. All data access is subject 
    to Supabase Row Level Security (RLS), ensuring that users can only see 
    rows they are authorized to view.

    Methods
    -------
    get_my_manager() -> dict
        Returns the manager row associated with the current user. Uses the
        authenticated user id to find the user's respective row.

    get_all_managers() -> list[dict]
        Returns a list of all managers.
    """
    def get_my_manager(self):
        result = (
            self.supabase
            .table("managers")
            .select("*")
            .eq("user_id", self.user_id)
            .execute()
        )

        return result.data[0]

    def get_all_managers(self):
        result = (
            self.supabase
            .table("managers")
            .select("*")
            .execute()
        )
        return result.data