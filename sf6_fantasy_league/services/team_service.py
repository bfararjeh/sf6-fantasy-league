import json
import re
from sf6_fantasy_league.services.base_service import BaseService

class TeamService(BaseService):
    """
    Service for managing teams. Handles team setup tasks such as naming, draft
    priority submission, and draft order assignment.

    Methods:
    create_team(team_name: str, player_list: list[str]) -> bool
        Creates a new team for the authenticated manager within their current 
        league. On success, inserts a new row into the teams table and links 
        it to the manager via managers.team_id.
        Returns True if successful
    """
    def create_team(self, team_name: str, player_list: list[str]):
        # validate state
        if not self.get_my_league():
            raise Exception("You are not in a league!")
        if self.get_my_team():
            raise Exception("You already have a team!")

        # verify attributes
        if len(team_name) < 4 or len(team_name) > 16:
            raise Exception("Team name must be inbetween 4 and 16 characters.")
        if not re.fullmatch(r'^\w+$', team_name):
            raise Exception("Team name must only include letters, numbers, and underscores.")
        if len(player_list) != 25:
            raise Exception("Draft list must contain exactly 25 players.")

        player_pool = self.verify_query(
            self.supabase.table("players")
            .select("name")
            .in_("name", player_list)
            )

        if len(player_pool.data) != 25:
            raise Exception(f"The submitted player list is invalid.")
    
        result = self.verify_query(
            self.supabase
            .table("teams")
            .insert({
                "league_id": self.get_my_league(),
                "team_name": team_name,
                "team_owner": self.user_id,
                "player_priority_list": json.dumps(player_list)
            })
        )

        return True