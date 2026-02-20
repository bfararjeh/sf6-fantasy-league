from datetime import datetime, timezone

import requests
from app.services.base_service import BaseService

class EventService():
    """
    Service for grabbing event data and score history.
    """
    def __init__(self, base: BaseService):
        self.base = base

    def __getattr__(self, name):
        return getattr(self.base, name)

    def get_events(self):  
        events = self.verify_query(
            self.supabase
            .table("events")
            .select("*")
        ).data

        BUCKET = "events"

        for event in events:
            image_name = event.get("image")
            if not image_name:
                event["image_bytes"] = None
                continue

            try:
                # validate image_name looks like a filename
                if not isinstance(image_name, str) or not image_name.endswith(".webp"):
                    event["image_bytes"] = None
                    continue

                # get public URL from storage
                image_url = self.supabase.storage.from_(BUCKET).get_public_url(image_name)
                if not image_url:
                    event["image_bytes"] = None
                    continue

                # fetch raw bytes
                response = requests.get(image_url)
                response.raise_for_status()
                event["image_bytes"] = response.content

            except Exception as e:
                # fail gracefully, store None if fetching fails
                event["image_bytes"] = None
        
        
        sorted_events = sorted(
            events,
            key=lambda x: datetime.fromisoformat(x["start_weekend"])
        )

        return sorted_events

    def get_distributions(self):  
        distributions = self.verify_query(
            self.supabase
            .table("distributions")
            .select("*")
        ).data

        return distributions

    def get_event_standings(self, event_id):   
        event = self.verify_query(
            self.supabase
            .table("events")
            .select("complete")
            .eq("id", event_id)
            .single()
        ).data

        if event["complete"] == False:
            raise Exception("This tournament is not complete yet!")
        score_history = self.verify_query(
            self.supabase
            .table("score_history")
            .select("player, rank, points")
            .eq("event", event_id)
        ).data

        return score_history
    
    def get_user_event_scores(self, team_id, event_id):
        '''
        Returns a players active team at the time of the tournament and how
        they placed
        '''

        # grab players of team and event date
        players = self.verify_query(
            self.supabase
            .table("team_players")
            .select("""
                player_name,
                joined_at,
                left_at
            """)
            .eq("team_id", team_id)
        ).data

        event = self.verify_query(
            self.supabase
            .table("events")
            .select("start_weekend, complete")
            .eq("id", event_id)
            .single()
        ).data

        if event["complete"] == False:
            raise Exception("This tournament is not complete yet!")

        # filter all players to active ones (at time of event)
        start_weekend = datetime.fromisoformat(event["start_weekend"].replace("Z", "+00:00"))
        filtered_players = [
            p for p in players
            if datetime.fromisoformat(p["joined_at"].replace("Z", "+00:00")) <= start_weekend
            and (
                p["left_at"] is None or
                datetime.fromisoformat(p["left_at"].replace("Z", "+00:00")) > start_weekend
            )
        ]

        # returns empty if no players were active at that point
        player_names = [p["player_name"] for p in filtered_players]
        if not player_names:
            return []

        # grab score history then assign score or 0 to each player.
        score_history = self.verify_query(
            self.supabase
            .table("score_history")
            .select("*")
            .eq("event", event_id)
            .in_("player", player_names)
        ).data

        score_lookup = {sh["player"]: {"points": sh["points"], "rank": sh["rank"]} for sh in score_history}
        standings = [
            {
                "player": p["player_name"],
                "points": score_lookup.get(p["player_name"], {"points": 0, "rank": None})["points"],
                "rank": score_lookup.get(p["player_name"], {"points": 0, "rank": None})["rank"]
            }
            for p in filtered_players
        ]
        return standings

    def get_league_event_scores(self, league_id, event_id):
        """
        Returns all users in a league's active teams (at the time of the event)
        and the scores of all players in those teams, keyed by username.
        """
        # fetch event date and completion
        event = self.verify_query(
            self.supabase
            .table("events")
            .select("start_weekend, complete")
            .eq("id", event_id)
            .single()
        ).data
        start_weekend = datetime.fromisoformat(event["start_weekend"].replace("Z", "+00:00"))

        if not event["complete"]:
            raise Exception("This tournament is not complete yet!")

        # fetch all teams in the league and their owners
        teams = self.verify_query(
            self.supabase
            .table("teams")
            .select("""
                team_id,
                owner:managers!teams_team_owner_fkey(
                    manager_name,
                    user_id
                )
            """)
            .eq("league_id", league_id)
        ).data

        if not teams:
            return {}

        # map team_id → username
        team_to_user = {t["team_id"]: t["owner"]["manager_name"] for t in teams}

        leaguemate_ids = list(team_to_user.keys())

        # fetch all players for these teams
        all_players = self.verify_query(
            self.supabase
            .table("team_players")
            .select("""
                team_id,
                player_name,
                joined_at,
                left_at
            """)
            .in_("team_id", leaguemate_ids)
        ).data

        # filter active players at event start
        active_players = [
            p for p in all_players
            if datetime.fromisoformat(p["joined_at"].replace("Z", "+00:00")) <= start_weekend
            and (p["left_at"] is None or datetime.fromisoformat(p["left_at"].replace("Z", "+00:00")) > start_weekend)
        ]

        if not active_players:
            return {team_to_user[tid]: {} for tid in leaguemate_ids}

        # fetch score history for active players
        player_names = [p["player_name"] for p in active_players]
        all_scores = self.verify_query(
            self.supabase
            .table("score_history")
            .select("*")
            .eq("event", event_id)
            .in_("player", player_names)
        ).data

        # build lookup for points + rank
        score_lookup = {sh["player"]: {"points": sh["points"], "rank": sh["rank"]} for sh in all_scores}

        # build final dict keyed by username
        standings_by_user = {}
        for team_id, username in team_to_user.items():
            team_players = [p for p in active_players if p["team_id"] == team_id]
            standings_by_user[username] = {
                p["player_name"]: {
                    "points": score_lookup.get(p["player_name"], {"points": 0, "rank": None})["points"],
                    "rank": score_lookup.get(p["player_name"], {"points": 0, "rank": None})["rank"]
                }
                for p in team_players
            }

        return standings_by_user

'''
 -- maybe in the future --
    def get_attendance(self, event_id=None):

        players = self.verify_query(
            self.supabase
            .table("players")
            .select("name")
        ).data

        tracked_set = set(p["name"] for p in players)
        attendance = []

        event_id = "1329192"
        page = 1
        per_page = 512
        total_pages = 1

        while page <= total_pages:
            result = self.base.graphql_request(
                """
                query EventPlayers($eventId: ID!, $page: Int!, $perPage: Int!) {
                    event(id: $eventId) {
                        entrants(query: { page: $page, perPage: $perPage }) {
                            pageInfo {
                                totalPages
                            }
                            nodes {
                                participants {
                                    gamerTag
                                }
                            }
                        }
                    }
                }
                """,
                variables={
                    "eventId": event_id,
                    "page": page,
                    "perPage": per_page
                }
            )

            entrants = result["data"]["event"]["entrants"]["nodes"]
            total_pages = result["data"]["event"]["entrants"]["pageInfo"]["totalPages"]

            for entrant in entrants:
                for participant in entrant["participants"]:
                    tag = participant["gamerTag"]
                    if tag in tracked_set:
                        attendance.append(tag)

            page += 1

        return attendance

 -- and in base service --
    def graphql_request(self, query: str, variables: dict = None):
        self.startgg_token = os.environ["STARTGG_API_KEY"]
        url = "https://api.start.gg/gql/alpha"
        headers = {
            "Authorization": f"Bearer {self.startgg_token}",
            "Content-Type": "application/json",
        }
        payload = {"query": query, "variables": variables or {}}

        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()
'''