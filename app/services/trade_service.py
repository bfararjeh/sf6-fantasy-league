from app.services.base_service import BaseService

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

    def get_open_requests(self):
            return []

    def create_player_request(self, receiver_id, initiator_player, receiver_player, window_id):
        return False

    def accept_request(self, request_id):
        return False

    def reject_request(self, request_id):
        return False

    def create_pool_request(self, give_player, receive_player, window_id):
        return False

    def get_pool_players(self):
        return []

    def get_trade_history(self, window_id):
        return []