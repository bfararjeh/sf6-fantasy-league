import re
from app.services.base_service import BaseService

class LeagueService():
    """
    Service for managing league-related operations for the authenticated user.
    This service inherits the `BaseService` class and provides methods for
    league creation, joining, leaving

    Methods:
    get_full_league_info() -> dict
        Returns the league info, draft status (if begun) and aesthetic 
        information as a dict.

    create_then_join_league(league_name: str) -> bool
        Creates a new league with the given name and assigns the current user to
        it. Returns the users new league ID.

    join_league(league_id: str) -> bool
        Assigns the authenticated user to an existing league specified by 
        `league_id`. Returns True if successful.

    leave_league() -> bool
        Removes the authenticated user from their current league and ensures
        their team is deleted. If they are the owner, they may only leave once
        they are the last member in their league. Owners delete leagues on
        leave. Returns True if successful.

    assign_draft_order(ordered_usernames: list[str]) -> bool
        Updates the league table row for the users league with a draft order,
        stored as a jsonb list of user IDs (ordered). Also assigns the first
        pick user via the ordered usernames. Returns True if successful.

    begin_draft() -> bool
        Runs through checks (league size, teams created, etc.) before 
        officially beginning the draft, allowing the current pick turn user
        to select their player. Returns True if successful.

    set_forfeit(forfeit: str) -> bool
        Sets the forfeit for a league. Returns True if successful.
    """
    def __init__(self, base: BaseService):
        self.base = base

    def __getattr__(self, name):
        return getattr(self.base, name)

    def get_full_league_info(self):
        '''
        Returns a combined dict of league aesthetics, members, and draft info (if draft started).
        '''
        # validate league state
        league_id = self.get_my_league()
        if not league_id:
            raise Exception("You are not currently in a league.")

        # grab all columns in league table, then all managers in that league
        data = self.verify_query(
            self.supabase
            .table("leagues")
            .select("""
                league_owner,
                forfeit,
                league_name,
                locked,
                draft_order,
                pick_turn,
                pick_direction,
                draft_complete,
                managers:managers!managers_league_id_fkey(
                    user_id,
                    manager_name
                )
            """)
            .eq("league_id", league_id)
            .single()
        ).data

        league = {
            "league_owner": data["league_owner"],
            "forfeit": data["forfeit"],
            "league_name": data["league_name"],
            "locked": data["locked"],
            "draft_order": data["draft_order"],
            "pick_turn": data["pick_turn"],
            "pick_direction": data["pick_direction"],
            "draft_complete": data["draft_complete"],
        }

        # build user_id -> manager_name map
        mates = data["managers"]  # list of {user_id, manager_name}
        manager_map = {m["user_id"]: m["manager_name"] for m in mates}

        # build the base dict
        result = {
            "league_id": league_id,
            "league_name": league["league_name"],
            "forfeit": league.get("forfeit"),
            "league_owner": league["league_owner"],
            "leaguemates": mates,
            "locked": league.get("locked")
        }

        # only include draft info if draft has begun i.e. locked is true
        try:
            result.update({
                "draft_order": [manager_map[uid] for uid in league["draft_order"]],
                "next_pick": manager_map[league["pick_turn"]],
                "pick_direction": league.get("pick_direction"),
                "draft_complete": league.get("draft_complete")
            })
        except:
            pass

        return result

    def create_then_join_league(self, league_name: str):
        # validating league state
        if self.get_my_league():
            raise Exception("User is already in a league.")
        
        # naming format rules
        if len(league_name) < 4 or len(league_name) > 24:
            raise Exception("League name must be inbetween 4 and 24 characters.")
        if not re.fullmatch(r"^[\w']+$", league_name):
            raise Exception("League name must only include letters, numbers, and underscores.")

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
        
        return self.get_my_league()

    def join_league(self, league_id: str):
        # validating league state
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
        # store league and team to reduce api queries
        my_league = self.get_my_league()
        my_team = self.get_my_team()

        # validating league state
        if not(my_league):
            raise Exception("User is not in a league.")
        
        league = self.verify_query(
            self.supabase
            .table("leagues")
            .select("*")
            .eq("league_id", my_league)
            .single()
            )

        if league.data["locked"]:
            raise Exception("You cannot leave a league once the draft has begun.")
        
        # check if league is full
        members = self.verify_query(
            self.supabase
            .table("managers")
            .select("*")
            .eq("league_id", my_league)
            )
        
        # owners can leave then delete leagues they are the only members of
        # anyone else can leave a league they dont own anytime
        if league.data["league_owner"] == self.user_id:
            # make sure owner is last member
            if len(members.data) != 1:
                raise Exception("You cannot leave a league you own that is not empty!")

            # delete the users team first
            if my_team:
                self.verify_query(
                    self.supabase
                    .table("teams")
                    .delete()
                    .eq("team_id", my_team)
                )

            # delete the league
            self.verify_query(
                self.supabase
                .table("leagues")
                .delete()
                .eq("league_id", my_league)
            )

            return True
            
        else:
            #delete the users team first
            if my_team:
                self.verify_query(
                    self.supabase
                    .table("teams")
                    .delete()
                    .eq("team_id", my_team)
                )

            # remove the user from the league
            self.verify_query(
                self.supabase
                .table("managers")
                .update({"league_id": None})
                .eq("user_id", self.user_id)
                )
            
            return True
        
    def assign_draft_order(self, ordered_usernames: list[str]):
        league_id = self.get_my_league()
        if not league_id:
            raise Exception("You are not currently in a league.")

        # validation
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

        # check the provided usernames are accurate
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

        # updates draft order and pick turn
        draft_order = [manager_map[name] for name in ordered_usernames]

        self.verify_query(
            self.supabase
            .table("leagues")
            .update({
                "draft_order": draft_order,
                "pick_turn": draft_order[0]
            })
            .eq("league_owner", self.user_id)
        )

        return True
    
    def begin_draft(self):
        league_id = self.get_my_league()
        if not league_id:
            raise Exception("You are not currently in a league.")

        # validation
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
        
        if len(managers) != len(league["draft_order"]):
            raise Exception("The draft order must be updated before beginning the draft!")

        # update league/begin draft
        self.verify_query(
            self.supabase
            .table("leagues")
            .update({"locked": True})
            .eq("league_id", league_id)
            .eq("league_owner", self.user_id)
        )

        return True

    def set_forfeit(self, forfeit):
        league_id = self.get_my_league()
        if not league_id:
            raise Exception("You are not currently in a league.")
        
        # naming format rules
        if len(forfeit) < 4 or len(forfeit) > 64:
            raise Exception("Forfeit must be inbetween 4 and 64 characters.")
        if not re.fullmatch(r"^[\w']+$", forfeit):
            raise Exception("Forfeit must only include letters, numbers, and underscores.")
    
        # validation
        league = self.verify_query(
            self.supabase
            .table("leagues")
            .select("league_owner, locked")
            .eq("league_id", league_id)
            .single()
        ).data

        if league["league_owner"] != self.user_id:
            raise Exception("Only the league owner can set the forfeit")

        self.verify_query(
            self.supabase
            .table("leagues")
            .update({"forfeit": forfeit})
            .eq("league_id", league_id)
        )

        return True