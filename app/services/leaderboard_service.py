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
                    manager_name
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
            t["team_id"]: (t["owner"]["manager_name"] if t["owner"] else None)
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
                    "players": []
                }

            standings[team_id]["players"].append({
                "player_name": row["player_name"],
                "points": row["points"]
            })

        return [
            {
                "team_name": data["team_name"],
                "user_name": data["owner_username"],
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

        safe_favourites = []
        for f in favourites or []:
            try:
                safe_favourites.append(str(uuid.UUID(str(f))))
            except ValueError:
                pass  # skip invalid entries

        if safe_favourites:
            # grabbing data of all favourites and creating class objects
            rows = self.verify_query(
                self.supabase
                .table("teams")
                .select("""
                    team_id,
                    team_name,
                    owner:managers!teams_team_owner_fkey(
                        user_id,
                        manager_name
                    ),
                    roster:team_players(
                        team_id,
                        player_name,
                        points
                    )
                """)
                .in_("team_owner", safe_favourites)   # filter teams by owner user_id
            ).data

            fav_list = [
                Favourite(
                    uid=row["owner"]["user_id"],
                    username=row["owner"]["manager_name"],
                    team_id=row["team_id"],
                    team_name=row["team_name"]
                )
                for row in rows
                if row.get("owner") is not None
            ]

            rosters = [
                p
                for row in rows
                for p in (row.get("roster") or [])
            ]

            # formatting stuff
            from collections import defaultdict

            # aggregate players by team_id
            standings = defaultdict(
                lambda: {
                    "team_name": "",
                    "owner": "",
                    "owner_id": None,
                    "players": []
                }
            )

            for f in fav_list:
                standings[f.team_id]["team_name"] = f.team_name
                standings[f.team_id]["owner"] = f.username
                standings[f.team_id]["owner_id"] = f.id

            for row in rosters:
                team_id = row["team_id"]
                standings[team_id]["players"].append({
                    "player_name": row["player_name"],
                    "points": row["points"]
                })

            # convert to list with total points
            return [
                {
                    "team_name": data["team_name"],
                    "user_name": data["owner"],
                    "user_id": data["owner_id"],
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