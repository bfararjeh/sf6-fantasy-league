from app.services.base_service import BaseService
from datetime import datetime, timezone

class TradeService():
    """
    Service for managing trades.

    Methods:
    get_trade_windows() -> list
        Returns a list of all trade windows.
    
    get_open_requests() -> list
        Returns all open trade requests where the user is initiator or receiver.

    create_player_request(receiver_id, initiator_player, receiver_player, window_id) -> bool
        Creates a player-to-player trade request.

    accept_request(request_id) -> bool
        Accepts a trade request, executing the swap atomically.

    reject_request(request_id) -> bool
        Rejects and deletes a trade request.

    create_pool_request(give_player, receive_player, window_id) -> bool
        Executes an instant player-to-pool trade atomically.

    get_pool_players() -> list
        Returns all unclaimed players in the user's league.

    get_trade_history(window_id) -> list
        Returns all completed trades for the user's league in a given trade window.
    """
    def __init__(self, base: BaseService):
        self.base = base

    def __getattr__(self, name):
        return getattr(self.base, name)

    def get_trade_windows(self):
        result = self.verify_query((
            self.supabase
            .table("trade_windows")
            .select("*")
            .order("start_date", desc=False,)
        ))
        
        return result.data

    def get_open_requests(self, user_id):
        result = self.verify_query((
            self.supabase
            .table("trade_requests")
            .select("*")
            .or_(f"initiator_id.eq.{user_id},receiver_id.eq.{user_id}")
        ))
        
        return result.data

    def get_pool_players(self):
        league_id = self.get_my_league()
        if not league_id:
            raise Exception("You are not in a league.")

        # get all claimed players in this league
        claimed = self.verify_query(
            self.supabase
            .table("team_players")
            .select("player_name")
            .eq("league_id", league_id)
            .is_("left_at", None)
        )
        claimed_names = [p["player_name"] for p in claimed.data] if claimed else []

        if claimed_names:
            # get all players not in claimed list
            result = self.verify_query(
                self.supabase
                .table("players")
                .select("*")
                .not_.in_("name", claimed_names)
            )
            return result.data if result else []
        else:
            return []

    def get_trade_history(self):
        league_id = self.get_my_league()
        if not league_id:
            raise Exception("You are not in a league.")

        result = self.verify_query(
            self.supabase
            .table("trades")
            .select("*")
            .eq("league_id", league_id)
            .order("completed_at", desc=True)
        )
        return result.data if result else []

    def create_player_request(self, initiator_id, receiver_id, initiator_player, receiver_player):
        now = datetime.now(timezone.utc).isoformat()

        # get current trade window
        window = self.verify_query(
            self.supabase
            .table("trade_windows")
            .select("*")
            .lte("start_date", now)
            .gte("end_date", now)
            .limit(1)
        )
        if not window or not window.data:
            raise Exception("You are not in an active trade window!")
        window_id = window.data[0]["id"]

        # verify both users are in the same league
        initiator_league = self.get_my_league()
        if not initiator_league:
            raise Exception("You are not in a league!")

        receiver_data = self.verify_query(
            self.supabase
            .table("managers")
            .select("league_id")
            .eq("user_id", receiver_id)
            .single()
        )
        if not receiver_data or not receiver_data.data:
            raise Exception("Receiver not found.")
        if receiver_data.data["league_id"] != initiator_league:
            raise Exception("You are not in the same league as the receiver!")

        # verify initiator owns initiator_player
        initiator_team = self.get_my_team()
        if not initiator_team:
            raise Exception("You do not have a team!")

        if not self.verify_query(
            self.supabase
            .table("team_players")
            .select("roster_id")
            .eq("team_id", initiator_team)
            .eq("player_name", initiator_player)
            .is_("left_at", None)
        ).data:
            raise Exception(f"You do not own {initiator_player}!")

        # verify receiver owns receiver_player
        receiver_team = self.verify_query(
            self.supabase
            .table("teams")
            .select("team_id")
            .eq("league_id", initiator_league)
            .eq("team_owner", receiver_id)
            .single()
        )
        if not receiver_team or not receiver_team.data:
            raise Exception("Receiver does not have a team!")
        receiver_team_id = receiver_team.data["team_id"]

        if not self.verify_query(
            self.supabase
            .table("team_players")
            .select("roster_id")
            .eq("team_id", receiver_team_id)
            .eq("player_name", receiver_player)
            .is_("left_at", None)
        ).data:
            raise Exception(f"Receiver does not own {receiver_player}!")

        # verify trade limits for both users
        for user_id, label in [(initiator_id, "You have"), (receiver_id, "Receiver has")]:
            count = self.verify_query(
                self.supabase
                .table("trades")
                .select("trade_id")
                .eq("league_id", initiator_league)
                .eq("trade_window_id", window_id)
                .or_(f"initiator_id.eq.{user_id},receiver_id.eq.{user_id}")
            )
            if count and len(count.data) >= 2:
                raise Exception(f"{label} reached the trade limit for this window.")

        # create the request
        self.verify_query(
            self.supabase
            .table("trade_requests")
            .insert({
                "initiator_id": initiator_id,
                "receiver_id": receiver_id,
                "league_id": initiator_league,
                "initiator_player": initiator_player,
                "receiver_player": receiver_player,
                "trade_window_id": window_id,
            })
        )

        return True

    def accept_request(self, request_id):
        self.supabase.rpc("accept_trade_request", {
            "p_request_id": request_id,
            "p_receiver_id": self.user_id
        }).execute()
        return True

    def reject_request(self, request_id):
        self.verify_query(
            self.supabase
            .table("trade_requests")
            .delete()
            .eq("request_id", request_id)
            .eq("receiver_id", self.user_id)
        )
        return True

    def delete_request(self, request_id):
        self.verify_query(
            self.supabase
            .table("trade_requests")
            .delete()
            .eq("request_id", request_id)
            .eq("initiator_id", self.user_id)
        )
        return True

    def create_pool_request(self, give_player, receive_player):
        now = datetime.now(timezone.utc).isoformat()

        # get current trade window
        window = self.verify_query(
            self.supabase
            .table("trade_windows")
            .select("*")
            .lte("start_date", now)
            .gte("end_date", now)
            .limit(1)
        )
        if not window or not window.data:
            raise Exception("There is no active trade window.")
        window_id = window.data[0]["id"]

        # get league
        league_id = self.get_my_league()
        if not league_id:
            raise Exception("You are not in a league.")

        # execute via db function
        self.supabase.rpc("execute_pool_trade", {
            "p_initiator_id": self.user_id,
            "p_league_id": league_id,
            "p_window_id": window_id,
            "p_give_player": give_player,
            "p_receive_player": receive_player,
        }).execute()

        return True
