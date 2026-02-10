import uuid

from app.services.base_service import BaseService

class LeaderboardService():
    """
    Service for grabbing scores of players, their teams, and their leagues.

    Methods:
    get_my_standings() -> jsonb
        Returns the user's team's player standings

    get_leaguemate_standings() -> jsonb
        Returns the standings of all players in all teams of a user's league

    get_player_cum_points() -> jsonb
        Returns the total cumulative point standings of all players
    """
    def __init__(self, base: BaseService):
        self.base = base

    def __getattr__(self, name):
        return getattr(self.base, name)

    def get_leaguemate_standings(self):
        # validating league state
        my_league = self.get_my_league()

        if not my_league:
            raise Exception("You're not in a league!")

        data = self.verify_query(
            self.supabase
            .table("teams")
            .select("""
                team_id,
                team_name,
                owner:managers!teams_team_owner_fkey(
                    manager_name, 
                    user_id
                ),
                roster:team_players(
                    team_id,
                    player_name,
                    points
                )
            """)
            .eq("league_id", my_league)
        ).data

        team_name_map = {t["team_id"]: t["team_name"] for t in data}

        owner_map = {
            t["team_id"]: {
                "username": t["owner"]["manager_name"] if t["owner"] else None,
                "user_id": t["owner"]["user_id"] if t["owner"] else None
            }
            for t in data
        }

        rosters = [
            player
            for t in data
            for player in (t["roster"] or [])
        ]

        standings = {}

        # formatting stuff
        for row in rosters:
            team_id = row["team_id"]

            if team_id not in standings:
                standings[team_id] = {
                    "team_name": team_name_map.get(team_id),
                    "owner_username": owner_map.get(team_id),
                    "user_id": owner_map.get(team_id, {}).get("user_id"),
                    "players": []
                }

            standings[team_id]["players"].append({
                "player_name": row["player_name"],
                "points": row["points"]
            })

        return [
            {
                "team_name": data["team_name"],
                "user_name": data["owner_username"]["username"],
                "user_id": data["user_id"],
                "players": data["players"],
                "total_points": sum(p["points"] for p in data["players"])
            }
            for team_id, data in standings.items()
        ]

    def get_players(self):  
        players = self.verify_query(
            self.supabase
            .table("players")
            .select("*")
        ).data

        return players

    def get_global_stats(self):
        global_stats = self.verify_query(
            self.supabase
            .table("global_stats")
            .select("*")
            .order("run_at", desc=True)
            .limit(1)
        ).data
        
        return global_stats