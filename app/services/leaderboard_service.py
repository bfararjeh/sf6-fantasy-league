from app.services.base_service import BaseService

class LeaderboardService():
    """
    Service for grabbing scores of players, their teams, and their leagues.

    Methods:
    get_my_standings() -> jsonb
        Returns the user's team's player standings.

    get_leaguemate_standings() -> jsonb
        Returns the standings of all players in all teams of a user's league.

    get_player_cum_points() -> jsonb
        Returns the total cumulative point standings of all players.
    """
    def __init__(self, base: BaseService):
        self.base = base

    def __getattr__(self, name):
        return getattr(self.base, name)
    
    def get_my_standings(self):
        my_team = self.get_my_team()

        if not self.get_my_league():
            raise Exception("You're not in a league!")
        if not my_team:
            raise Exception("You do not own a team!")

        rows = self.verify_query(
            self.supabase
            .table("team_players")
            .select("player_name, points")
            .eq("team_id", my_team)
        ).data

        return [{
            "name": "My Team",
            "players": [
                {"id": r["player_name"], "points": r["points"]}
                for r in rows
            ],
            "total_points": sum(r["points"] for r in rows)
        }]
    
    def get_leaguemate_standings(self):
        my_league = self.get_my_league()

        if not my_league:
            raise Exception("You're not in a league!")
        
        league = self.verify_query(
            self.supabase
            .table("leagues")
            .select("draft_complete")
            .eq("league_id", my_league)
        ).data

        if league[0]["draft_complete"] == False:
            raise Exception("The draft isn't complete yet!")

        teams = self.verify_query(
            self.supabase
            .table("teams")
            .select("team_id, team_name")
            .eq("league_id", my_league)
        ).data

        team_name_map = {t["team_id"]: t["team_name"] for t in teams}

        owners = self.verify_query(
            self.supabase
            .table("teams")
            .select("team_id, team_owner, managers(manager_name)")
            .eq("league_id", my_league)
        ).data

        owner_map = {
            row["team_id"]: row["managers"]["manager_name"]
            for row in owners
        }
        
        rosters = self.verify_query(
            self.supabase
            .table("team_players")
            .select("team_id, player_name, points")
            .eq("league_id", my_league)
        )

        standings = {}

        for row in rosters.data:
            team_id = row["team_id"]

            if team_id not in standings:
                standings[team_id] = {
                    "team_name": team_name_map.get(team_id),
                    "owner_username": owner_map.get(team_id),
                    "players": []
                }

            standings[team_id]["players"].append({
                "player_name": row["player_name"],
                "points": row["points"]
            })

        return [
            {
                "name": data["team_name"],
                "owner": data["owner_username"],
                "players": data["players"],
                "total_points": sum(p["points"] for p in data["players"])
            }
            for team_id, data in standings.items()
        ]
    
    def get_player_cum_points(self):
        
        players = self.verify_query(
            self.supabase
            .table("players")
            .select("*")
        ).data

        return players