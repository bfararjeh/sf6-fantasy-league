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
    def create_team(self, team_name: str):
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
    
        self.verify_query(
            self.supabase
            .table("teams")
            .insert({
                "league_id": self.get_my_league(),
                "team_owner": self.user_id,
                "team_name": team_name
            })
        )

        return True

    def pick_player(self, player_name: str):
        # validate state
        if not self.get_my_league():
            raise Exception("You are not in a league!")
        if not self.get_my_team():
            raise Exception("You do not have a team!")

        league = self.verify_query(
            self.supabase
            .table("leagues")
            .select("draft_order, pick_turn")
            .eq("league_id", self.get_my_league())
        ).data

        if league[0]["pick_turn"] != self.user_id:
            raise Exception("It's not your turn to pick a player!")
        
        result = self.verify_query(
            self.supabase
            .table("players")
            .select("name")
            .eq("name", player_name)
        )

        if not result.data:
            raise Exception("Entered player is not in the player pool!")
        
        taken_players = self.verify_query(
            self.supabase
            .table("team_players")
            .select("player_name, team_id")
            .eq("league_id", self.get_my_league())
        )

        if player_name in {row["player_name"] for row in taken_players.data}:
            raise Exception("This player has already been picked!")
        
        team_player_count = sum(
            1 for row in taken_players.data if row["team_id"] == self.get_my_team()
        )

        if team_player_count == 5:
            raise Exception("This team is full!")
        
        self.verify_query(
            self.supabase
            .table("team_players")
            .insert({
                "league_id": self.get_my_league(),
                "team_id": self.get_my_team(),
                "player_name": player_name,
                })
            )
        
        draft_order = league[0]["draft_order"]
        next_pick = draft_order[(draft_order.index(league[0]["pick_turn"])+1)%len(draft_order)] 
    
        self.verify_query(
            self.supabase
            .table("leagues")
            .update({"pick_turn": next_pick})
            .eq("league_id", self.get_my_league())
        )
    
        return True