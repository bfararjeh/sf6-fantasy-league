import json
from uuid import uuid4
from sf6_fantasy_league.services.base_service import BaseService

class TeamService(BaseService):
    def submit_draft_priority(self, player_list: list[str]):
        if len(player_list) != 25:
            raise Exception("Draft list must contain exactly 25 players.")

        player_pool = self.verify_query(
            self.supabase.table("players")
            .select("name")
            .in_("name", player_list)
            )

        if not player_pool.data or len(player_pool.data) != 25:
            existing_names = [p["name"] for p in player_pool.data] if player_pool.data else []
            missing = set(player_list) - set(existing_names)
            raise Exception(f"The following players do not exist: {missing}")

        result = self.verify_query(
            self.supabase.table("managers")
            .update({"player_priority_list": json.dumps(player_list)})
            .eq("user_id", self.user_id)
            )

        return True
    
    def assign_draft_order(self, ordered_usernames):

        if not ordered_usernames:
            raise Exception("Draft order list cannot be empty.")

        manager = self.get_my_user()
        league_id = manager["league_id"]

        if not league_id:
            raise Exception("You are not currently in a league.")

        league = self.verify_query(
            self.supabase
            .table("leagues")
            .select("league_owner, locked")
            .eq("league_id", league_id)
            .single()
        ).data

        if league["league_owner"] != self.user_id:
            raise Exception("Only the league owner can set draft order.")

        if league["locked"]:
            raise Exception("Cannot modify draft order once the draft has begun.")

        managers = self.verify_query(
            self.supabase
            .table("managers")
            .select("user_id, manager_name")
            .eq("league_id", league_id)
        ).data

        manager_map = {m["manager_name"]: m["user_id"] for m in managers}

        if len(ordered_usernames) != len(managers):
            raise Exception("Draft order list must include every manager in the league.")

        for username in ordered_usernames:
            if username not in manager_map:
                raise Exception(f"Invalid username in draft list: {username}")

        updates = []
        for i, username in enumerate(ordered_usernames, start=1):
            user_id = manager_map[username]
            updates.append(self.verify_query(
                self.supabase
                .table("managers")
                .update({"draft_order": i})
                .eq("user_id", user_id)
                ))

        return True

    def begin_draft(self):
        manager = self.get_my_user()
        league_id = manager["league_id"]

        if not league_id:
            raise Exception("You are not in a league.")

        league = self.verify_query(
            self.supabase
            .table("leagues")
            .select("league_owner, locked")
            .eq("league_id", league_id)
            .single()
        ).data

        managers = self.verify_query(
            self.supabase
            .table("managers")
            .select("user_id, player_priority_list, draft_order")
            .eq("league_id", league_id)
        ).data

        if league["league_owner"] != self.user_id:
            raise Exception("Only the league owner can begin the draft.")

        if league["locked"]:
            raise Exception("Draft already started. League is locked.")

        if len(managers) < 2:
            raise Exception("At least 2 managers are required to start a draft.")

        for m in managers:
            if not m["player_priority_list"]:
                raise Exception("All managers must submit their draft lists before drafting.")
            
            if not m["draft_order"]:
                raise Exception("Draft order must be assigned first.")

        result = self.verify_query(
            self.supabase
            .table("leagues")
            .update({"locked": True})
            .eq("league_id", league_id)
        )

        return True