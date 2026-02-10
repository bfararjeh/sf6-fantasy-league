import re
from app.services.base_service import BaseService

class TeamService():
    """
    Service for managing teams. Handles team setup tasks such as naming, draft
    priority submission, and draft order assignment.

    Methods:
    get_my_team_name() -> str
        Returns the users team name as a string.
        
    create_team(team_name: str) -> bool
        Creates a new team for the authenticated manager within their current 
        league. Returns the users new team ID.

    pick_player(player_name: str) -> bool
        Adds a player to a user's team within the game specification. Returns 
        True if successful.
    """
    def __init__(self, base: BaseService):
        self.base = base

    def __getattr__(self, name):
        return getattr(self.base, name)

    def get_full_team_info(self):
        team_id = self.get_my_team()
        if not team_id:
            raise Exception("You do not own a team!")
        
        data = self.verify_query(
            self.supabase
            .table("teams")
            .select("""
                team_name,
                team_players(
                    player_name,
                    points,
                    players(region),
                    joined_at,
                    left_at
                )
            """)
            .eq("team_id", team_id)
            .single()
        ).data

        team_name = data["team_name"]
        rows = data["team_players"]

        return {
            "team_name": team_name,
            "team_id": team_id,
            "players": [
                {
                    "id": r["player_name"],
                    "points": r["points"],
                    "region": r["players"]["region"],
                    "joined_at": r["joined_at"],
                    "left_at": r["left_at"]
                }
                for r in rows
            ],
            "total_points": sum(r["points"] for r in rows)
        }
 
    def create_team(self, team_name: str):
        my_league = self.get_my_league()
        # validation
        if not my_league:
            raise Exception("You are not in a league!")
        if self.get_my_team():
            raise Exception("You already have a team!")

        # verify attributes
        if len(team_name) < 4 or len(team_name) > 24:
            raise Exception("Team name must be inbetween 4 and 24 characters.")
        if not re.fullmatch(r"^[\w']+$", team_name):
            raise Exception("Team name must only include letters, numbers, and underscores.")
    
        # insert new team into table
        self.verify_query(
            self.supabase
            .table("teams")
            .insert({
                "league_id": my_league,
                "team_owner": self.user_id,
                "team_name": team_name
            })
        )

        return self.get_my_team()

    def pick_player(self, player_name: str):
        my_league = self.get_my_league()
        my_team = self.get_my_team()

        # validate state
        if not my_league:
            raise Exception("You are not in a league!")
        if not self.get_my_team():
            raise Exception("You do not have a team!")

        # check if its the clients turn to pick
        league = self.verify_query(
            self.supabase
            .table("leagues")
            .select("draft_order, pick_turn, pick_direction, locked, draft_complete")
            .eq("league_id", my_league)
        ).data

        if league[0]["locked"] == False:
            raise Exception("The draft hasn't begun yet!")

        if league[0]["draft_complete"] == True:
            raise Exception("The draft is over!")

        if league[0]["pick_turn"] != self.user_id:
            raise Exception("It's not your turn to pick a player!")
        
        # check if player exists
        result = self.verify_query(
            self.supabase
            .table("players")
            .select("name")
            .eq("name", player_name)
        )

        if not result.data:
            raise Exception("Entered player is not in the player pool!")
        
        # check player is available and team has room
        taken_players = self.verify_query(
            self.supabase
            .table("team_players")
            .select("player_name, team_id, left_at")
            .eq("league_id", my_league)
        )
        
        team_player_count = sum(
            1 for row in taken_players.data if row["team_id"] == my_team and row["left_at"] == None
        )

        if team_player_count == 5:
            raise Exception("This team is full!")
        if player_name in {row["player_name"] for row in taken_players.data}:
            raise Exception("This player has already been picked!")
        
        # update pick turn with snake draft logic
        draft_order = league[0]["draft_order"]
        direction = league[0]["pick_direction"]
        current = league[0]["pick_turn"]

        idx = draft_order.index(current)
        next_idx = idx + direction

        if next_idx >= len(draft_order) or next_idx < 0:
            direction *= -1
            next_idx = idx

            if direction == -1 and team_player_count == 4:
                self.verify_query(
                    self.supabase
                    .table("leagues")
                    .update({
                        "draft_complete": True
                    })
                    .eq("league_id", my_league)
                )

        next_pick = draft_order[next_idx]
            
        self.verify_query(
            self.supabase
            .table("leagues")
            .update({
                "pick_turn": next_pick,
                "pick_direction": direction
            })
            .eq("league_id", my_league)
        )
    
        # insert player into table
        self.verify_query(
            self.supabase
            .table("team_players")
            .insert({
                "league_id": my_league,
                "team_id": self.get_my_team(),
                "player_name": player_name,
                })
            )
        
        return True