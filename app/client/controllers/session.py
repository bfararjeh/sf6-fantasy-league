from app.services.leaderboard_service import LeaderboardService
from app.services.team_service import TeamService
from app.services.league_service import LeagueService

class Session:
    '''
    Class responsible with storing all cached data for the application.
    '''
    VERSION = "1.0.0"

    # authenticated supabase session
    auth_base = None

    # username and user id
    user = None
    user_id = None

    '''
    cached system state info
    blocking defaults True: block everything if connection fails
    '''
    blocking_state = True
    warning_message = None
    banner_message = None

    # cached league info
    current_league_id = None
    current_league_name = None
    league_forfeit = None
    is_league_owner = False
    leaguemates = {}
    draft_order = []
    next_pick = None

    # services locked and loaded
    team_service = None
    league_service = None
    leaderboard_service = None

    @classmethod
    def init_services(cls):
        if not cls.auth_base:
            raise RuntimeError("Cannot initialize services without auth_base.")

        # this could be in aesthetics, but its fixed so putting it here
        cls.user = cls.auth_base.get_my_username()
        cls.user_id = cls.auth_base.user_id

        cls.team_service = TeamService(cls.auth_base)
        cls.league_service = LeagueService(cls.auth_base)
        cls.leaderboard_service = LeaderboardService(cls.auth_base)

        cls.init_aesthetics()
    
    @classmethod
    def init_aesthetics(cls):
        # system state info
        try:
            system_state = cls.auth_base.get_system_state()
            cls.blocking_state = system_state["blocking"]
            cls.banner_message = system_state["banner_message"]
            cls.warning_message = system_state["warning_message"]

        except Exception as e:
            cls.blocking_state = True
            cls.banner_message = None
            cls.warning_message = "CRITICAL ERROR: Unable to connect to database."
            return

        # league data
        try:
            league_data = cls.league_service.get_full_league_info() or None

            cls.current_league_id = league_data["league_id"] or None
            cls.current_league_name = league_data["league_name"] or None
            cls.league_forfeit = league_data["forfeit"] or None
            cls.is_league_owner = True if league_data["league_owner"] == cls.user_id else False
            cls.leaguemates = league_data["leaguemates"]
            cls.draft_order = league_data["draft_order"]
            cls.next_pick = league_data["next_pick"]

        except Exception:
            cls.current_league_id = None
            cls.current_league_name = None
            cls.league_forfeit = None
            cls.is_league_owner = False
            cls.leaguemates = {}
            cls.draft_order = []
            cls.next_pick = None

        # team id
        try:
            cls.current_team_id = cls.team_service.get_my_team() or None
        except Exception:
            cls.current_team_id = None

        # team name
        try:
            cls.current_team_name = cls.team_service.get_my_team_name() or None
        except Exception:
            cls.current_team_name = None

    @classmethod
    def reset(cls):
        cls.auth_base = None

        cls.user = None
        cls.user_id = None

        cls.blocking_state = True
        cls.warning_message = None
        cls.banner_message = None

        cls.current_league_id = None
        cls.current_league_name = None
        cls.league_forfeit = None
        cls.is_league_owner = False
        cls.leaguemates = {}
        cls.draft_order = []
        cls.next_pick = None

        cls.team_service = None
        cls.league_service = None
        cls.leaderboard_service = None