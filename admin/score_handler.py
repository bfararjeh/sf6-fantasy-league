import ast
from app.db.admin_client import get_admin_client

class ScoreHandler:
    def __init__(self, client):
        self.admin_client = client

    def update_score_history(self, event_id, raw_players):
        event = (
            self.admin_client.table("events")
            .select("*")
            .eq("id", event_id)
            .execute()
        ).data
        if not event:
            print(f"No event found with ID {event_id}. Aborting.")
            return
        
        event = event[0]
        tier = event["tier"]

        existing_scores = (
            self.admin_client.table("score_history")
            .select("id")
            .eq("event", event_id)
            .execute()
        ).data
        if existing_scores:
            print(f"Score history already exists for event {event_id}. Aborting.")
            return

        distribution = (
            self.admin_client.table("distributions")
            .select("dist")
            .eq("tier", tier)
            .execute()
        ).data
        if not distribution or "dist" not in distribution[0]:
            raise ValueError(f"Invalid distribution for tier {tier}")
        
        dist = {int(k): v for k, v in distribution[0]['dist'].items()}
        sorted_ranks = sorted(dist.keys())
        ordered_players = ast.literal_eval(raw_players)

        if len(ordered_players) > 64:
            raise ValueError("Max 64 players allowed")

        if len(ordered_players) == 0:
            raise ValueError("Player list empty")

        inserts = []
        for idx, player in enumerate(ordered_players, start=1):
            applicable_rank = max(r for r in sorted_ranks if r <= idx)
            points = dist[applicable_rank]
            inserts.append({
                "player": player,
                "event": event_id,
                "rank": applicable_rank,
                "points": points
            })

        try:
            self.admin_client.table("score_history").insert(inserts).execute()
            print(f"Inserted scores for {len(inserts)} players for event {event_id}.")
        except Exception as e:
            raise Exception(f"Failed to insert score_history: {e}")

        try:
            self.admin_client.rpc(fn="master_update", params=[{"p_event": event_id}]).execute()
            print("Updated cum points, team player points, and team score history for all teams.")
        except Exception as e:
            raise Exception(f"Failed to update points: {e}")

if __name__ == "__main__":
    handler = ScoreHandler(get_admin_client())
    handler.populate_scores()