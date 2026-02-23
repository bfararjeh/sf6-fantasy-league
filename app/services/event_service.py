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
        if team_id == None:
            raise Exception("You don't have a team!")

        event = self.verify_query(
            self.supabase
            .table("events")
            .select("start_weekend, complete")
            .eq("id", event_id)
            .single()
        ).data

        if event["complete"] == False:
            raise Exception("This tournament is not complete yet!")

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
            return None

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
        if league_id == None:
            raise Exception("You are not part of a league!")
        
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
            return None

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
            return {}

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

        standings_by_user = {}
        for team_id, username in team_to_user.items():
            team_players = [p for p in active_players if p["team_id"] == team_id]
            if team_players:
                standings_by_user[username] = {
                    p["player_name"]: {
                        "points": score_lookup.get(p["player_name"], {"points": 0, "rank": None})["points"],
                        "rank": score_lookup.get(p["player_name"], {"points": 0, "rank": None})["rank"]
                    }
                    for p in team_players
                }

        return standings_by_user

    def get_player_points_timeline(self, player, joined_at=None, left_at=None):
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

        def parse_dt(dt_str):
            if dt_str is None:
                return None
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt

        joined_dt = parse_dt(joined_at)
        left_dt = parse_dt(left_at) or datetime.max.replace(tzinfo=timezone.utc)

        history = [
            sh for sh in score_history
            if joined_dt <= parse_dt(sh["events"]["start_weekend"]) <= left_dt
        ]
        history.sort(key=lambda x: x["events"]["start_weekend"])
        running = 0
        timeline = []
        for h in history:
            running += h["points"]
            timeline.append({
                "event_name": h["events"]["name"],
                "event_date": h["events"]["start_weekend"],
                "points_gained": h["points"],
                "points_after": running
            })
        return timeline