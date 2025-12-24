import re
from sf6_fantasy_league.db.supabase_client import get_supabase_client
from sf6_fantasy_league.services.base_service import BaseService

class LeagueService(BaseService):
    """
    Service for managing league-related operations for the authenticated user.

    This service inherits the `BaseService` class.

    This class provides methods to retrieve the current user's manager row,
    create and join a new league, join an existing league, and leave their 
    current league.

    Methods
    -------
    get_my_manager() -> dict
        Returns the manager row associated with the authenticated user.

    create_and_join_league(league_name: str) -> bool
        Creates a new league with the given name and assigns the current user to
        it.

    join_league(league_id: str) -> bool
        Assigns the authenticated user to an existing league specified by 
        `league_id`.

    leave_league() -> bool
        Removes the authenticated user from their current league.
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

    def create_and_join_league(self, league_name: str):
        manager = self.get_my_manager()
        if manager["league_id"]:
            raise Exception("User is already in a league.")
        
        if len(league_name) < 6 or len(league_name) > 24:
            raise Exception("League name must be inbetween 6 and 24 characters.")
        if not re.fullmatch(r'^[\w ]+$', league_name):
            raise Exception("League name must only include letters, numbers, underscores, and spaces.")

        # create league
        result = (
            self.supabase
            .table("leagues")
            .insert({"league_name": league_name})
            .execute()
            )

        if not result.data:
            raise Exception(f"Failed to create league: {result.data}")

        league_id = result.data[0]["league_id"]

        # update manager row
        update = (
            self.supabase
            .table("managers")
            .update({"league_id": league_id})
            .eq("user_id", self.user_id)
            .execute()
            )
        
        return True

    def join_league(self, league_id: str):
        manager = self.get_my_manager()
        if manager["league_id"]:
            raise Exception("You are already in a league.")

        # check if league exists
        try:
            check = (
                self.supabase
                .table("leagues")
                .select("*")
                .eq("league_id", league_id)
                .execute()
                )
        except Exception as e:
            print("League not found.")

        update = (
            self.supabase
            .table("managers")
            .update({"league_id": league_id})
            .eq("user_id", self.user_id)
            .execute()
            )

        return True

    def leave_league(self):
        manager = self.get_my_manager()
        if not manager["league_id"]:
            raise Exception("You are not in a league.")

        update = (
            self.supabase
            .table("managers")
            .update({"league_id": None})
            .eq("user_id", self.user_id)
            .execute()
            )

        return True