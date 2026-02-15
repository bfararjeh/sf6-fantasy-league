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

        return events

    def get_distributions(self):  
        distributions = self.verify_query(
            self.supabase
            .table("distributions")
            .select("*")
        ).data

        return distributions

    def get_event_score_history(self, event_id):  
        score_history = self.verify_query(
            self.supabase
            .table("score_history")
            .select("*")
            .eq("event", event_id)
        ).data

        return score_history

    def get_player_score_history(self, player, joined_at=None, left_at=None):
        score_history = self.verify_query(
            self.supabase
            .table("score_history")
            .select("""
                events(name, start_weekend),
                rank,
                points
            """)
            .eq("player", player)
        ).data

        if joined_at:
            filtered_history = [
                sh for sh in score_history
                if joined_at <= sh["events"]["start_weekend"] <= (left_at or datetime.max)
            ]
            return filtered_history

        return score_history

    def get_player_points_timeline(self, player, joined_at=None, left_at=None):
        history = self.get_player_score_history(player, joined_at, left_at)

        history.sort(key=lambda x: x["events"]["start_weekend"])

        running = 0
        timeline = []

        for h in history:
            before = running
            running += h["points"]

            timeline.append({
                "event_name": h["events"]["name"],
                "event_date": h["events"]["start_weekend"],
                "points_gained": h["points"],
                "points_before": before,
                "points_after": running
            })

        return timeline

    def get_team_score_history(self, team_id):  
        score_history = self.verify_query(
            self.supabase
            .table("team_score_history")
            .select("""
                points,
                events(name, start_weekend)
            """)
            .eq("team", team_id)
        ).data

        return score_history

    def get_team_points_timeline(self, team_id):
        history = self.get_team_score_history(team_id)

        history.sort(key=lambda x: x["events"]["start_weekend"])

        running = 0
        timeline = []

        for h in history:
            before = running
            running += h["points"]

            timeline.append({
                "event_name": h["events"]["name"],
                "event_date": h["events"]["start_weekend"],
                "points_gained": h["points"],
                "points_before": before,
                "points_after": running
            })

        return timeline

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