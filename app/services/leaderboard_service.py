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

    get_favourite_standings(favourites: list[str]) -> jsonb
        Returns the standings of all managers in the users favourite list.

    get_player_cum_points() -> jsonb
        Returns the total cumulative point standings of all players
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
        # validating league state
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

        # grabbing all teams and owners (knowing the draft is done)
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
        
        # grabbing all elements in team_players
        rosters = self.verify_query(
            self.supabase
            .table("team_players")
            .select("team_id, player_name, points")
            .eq("league_id", my_league)
        )

        standings = {}

        # formatting stuff
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

    def get_favourite_standings(self, favourites):

        # helper class for storing favourites data and reducing api queries
        class Favourite():
            def __init__(self, uid, team_name, team_id, username):
                self.id = uid
                self.team_name = team_name
                self.team_id = team_id
                self.username = username

            def __repr__(self):
                return (
                    f"Favourite(\n"
                    f"id={self.id!r},\n"
                    f"username={self.username!r},\n"
                    f"team_id={self.team_id!r},\n"
                    f"team_name={self.team_name!r}\n"
                    f")"
                )

        # validating passed favourites list
        if not all(isinstance(f, str) and uuid.UUID(f) for f in favourites):
            raise Exception("Favourites must be of type list[UUID: str].")

        # grabbing data of all favourites and creating class objects
        owners = self.verify_query(
            self.supabase
            .table("teams")
            .select("team_id, team_owner, team_name, managers!inner(manager_name, user_id)")
            .in_("managers.user_id", favourites)
        ).data

        fav_list = []

        for row in owners:
            fav_list.append(Favourite(
                uid = row["managers"]["user_id"],
                username = row["managers"]["manager_name"],
                team_id= row["team_id"],
                team_name = row["team_name"]
            ))
        
        team_id_list = {
            f.team_id for f in fav_list
        }

        # grabbing all elements in team_players
        rosters = self.verify_query(
            self.supabase
            .table("team_players")
            .select("team_id, player_name, points")
            .in_("team_id", team_id_list)
        ).data

        # formatting stuff
        from collections import defaultdict

        # aggregate players by team_id
        standings = defaultdict(lambda: {"team_name": "", "owner": "", "players": []})

        for f in fav_list:
            standings[f.team_id]["team_name"] = f.team_name
            standings[f.team_id]["owner"] = f.username

        for row in rosters:
            team_id = row["team_id"]
            standings[team_id]["players"].append({
                "player_name": row["player_name"],
                "points": row["points"]
            })

        # convert to list with total points
        return [
            {
                "name": data["team_name"],
                "owner": data["owner"],
                "players": data["players"],
                "total_points": sum(p["points"] for p in data["players"])
            }
            for data in standings.values()
        ]

    def get_players(self):  
        players = self.verify_query(
            self.supabase
            .table("players")
            .select("*")
        ).data

        return players