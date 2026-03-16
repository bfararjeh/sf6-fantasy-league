from app.services.base_service import BaseService

class TradeService():
    """
    Service for managing trades.

    Methods:
    get_my_team_name() -> str
        Returns the users team name as a string.
        
    create_team(team_name: str) -> bool
        Creates a new team for the authenticated manager within their current 
        league. Returns the users new team ID.

    pick_player(player_name: str) -> bool
        Adds a player to a user's team within the game specification. Returns 
        True if successful.
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