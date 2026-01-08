import re
from sf6_fantasy_league.services.base_service import BaseService

class LeagueService(BaseService):
    """
    Service for managing league-related operations for the authenticated user.
    This service inherits the `BaseService` class and provides methods for
    league creation, joining, leaving

    Methods:
    create_then_join_league(league_name: str) -> bool
        Creates a new league with the given name and assigns the current user to
        it. 
        Returns True if successful.

    join_league(league_id: str) -> bool
        Assigns the authenticated user to an existing league specified by 
        `league_id`.
        Returns True if successful.

    leave_league() -> bool
        Removes the authenticated user from their current league.
        Returns True if successful.

    assign_draft_order(ordered_usernames: list[str]) -> bool
        Assigns draft positions to all managers in the league based on the order
        of usernames provided. Can only be done by the league owner and only
        before the draft is locked.
        Returns True if successful.
    """
    def create_then_join_league(self, league_name: str):
        if self.get_my_league():
            raise Exception("User is already in a league.")
        
        # naming format rules
        if len(league_name) < 6 or len(league_name) > 24:
            raise Exception("League name must be inbetween 6 and 24 characters.")
        if not re.fullmatch(r'^[\w ]+$', league_name):
            raise Exception("League name must only include letters, numbers, underscores, and spaces.")

        # create league
        result = self.verify_query(
            self.supabase
            .table("leagues")
            .insert({
                "league_name": league_name,
                "league_owner": self.user_id,
                "locked": False
                })
            )

        # join league
        self.verify_query(
            self.supabase
            .table("managers")
            .update({"league_id": result.data[0]["league_id"]})
            .eq("user_id", self.user_id)
            )
        
        return True

    def join_league(self, league_id: str):
        if self.get_my_league():
            raise Exception("User is already in a league.")

        # check if league exists
        try:
            check = self.verify_query(
                self.supabase
                .table("leagues")
                .select("league_id, locked")
                .eq("league_id", league_id)
                .single()
                )
        except Exception as e:
            raise Exception("League not found.")

        if check.data["locked"]:
            raise Exception("League is currently closed for joining.")
        
        # check if league is full
        members = self.verify_query(
            self.supabase
            .table("managers")
            .select("*")
            .eq("league_id", league_id)
            )
        
        if len(members.data) >= 5:
            raise Exception("League is full.")

        self.verify_query(
            self.supabase
            .table("managers")
            .update({"league_id": league_id})
            .eq("user_id", self.user_id)
            )

        return True

    def leave_league(self):
        if not(self.get_my_league()):
            raise Exception("User is not in a league.")

        # get the league id and check if its locked
        league = self.verify_query(
            self.supabase
            .table("leagues")
            .select("*")
            .eq("league_id", self.get_my_league())
            .single()
            )
        
        if league.data["locked"]:
            raise Exception("This league has been locked.")

        # remove the user from the league
        self.verify_query(
            self.supabase
            .table("managers")
            .update({"league_id": None})
            .eq("user_id", self.user_id)
            )

        return True

    def assign_draft_order(self, ordered_usernames: list[str]):

        if not ordered_usernames:
            raise Exception("Draft order list cannot be empty.")

        league_id = self.get_my_league()

        if not league_id:
            raise Exception("You are not currently in a league.")

        league = self.verify_query(
            self.supabase
            .table("leagues")
            .select("league_owner, locked")
            .eq("league_id", league_id)
            .single()
        ).data

        if league["league_owner"] != self.user_id:
            raise Exception("Only the league owner can set draft order.")

        if league["locked"]:
            raise Exception("Cannot modify draft order once the draft has begun.")

        managers = self.verify_query(
            self.supabase
            .table("managers")
            .select("user_id, manager_name")
            .eq("league_id", league_id)
        ).data

        manager_map = {m["manager_name"]: m["user_id"] for m in managers}

        if len(ordered_usernames) != len(managers):
            raise Exception("Draft order list must consist of all managers in the league.")

        for username in ordered_usernames:
            if username not in manager_map:
                raise Exception(f"Invalid username in draft list: {username}")

        draft_order = [manager_map[name] for name in ordered_usernames]

        self.verify_query(
            self.supabase
            .table("leagues")
            .update({"draft_order": draft_order})
            .eq("league_owner", self.user_id)
        )

        self.verify_query(
            self.supabase
            .table("leagues")
            .update({"pick_turn": draft_order[0]})
            .eq("league_owner", self.user_id)
        )

        return True
    
    def begin_draft(self):

        league_id = self.get_my_league()

        if not league_id:
            raise Exception("You are not currently in a league.")

        league = self.verify_query(
            self.supabase
            .table("leagues")
            .select("league_owner, locked, draft_order")
            .eq("league_id", league_id)
            .single()
        ).data

        if league["league_owner"] != self.user_id:
            raise Exception("Only the league owner can begin the draft.")

        if league["locked"]:
            raise Exception("The draft has already begun!")

        if league["draft_order"] is None:
            raise Exception("Draft order must be set before beginning the draft.")
        
        managers = self.verify_query(
            self.supabase
            .table("managers")
            .select("user_id")
            .eq("league_id", league_id)
        ).data

        if len(managers) < 2:
            raise Exception("A league must have at least 2 managers to begin the draft.")

        self.verify_query(
            self.supabase
            .table("leagues")
            .update({"locked": True})
            .eq("league_id", league_id)
            .eq("league_owner", self.user_id)
        )

        return True