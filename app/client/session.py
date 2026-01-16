from app.services.leaderboard_service import LeaderboardService
from app.services.team_service import TeamService
from app.services.league_service import LeagueService

class Session:
    VERSION = "1.0.0"

    user = None
    current_league_name = None
    current_league_id = None
    is_league_owner = False
    league_forfeit = None

    auth_base = None
    team_service = None
    league_service = None
    leaderboard_service = None

    @classmethod
    def init_services(cls):
        if not cls.auth_base:
            raise RuntimeError("Cannot initialize services without auth_base.")

        cls.team_service = TeamService(cls.auth_base)
        cls.league_service = LeagueService(cls.auth_base)
        cls.leaderboard_service = LeaderboardService(cls.auth_base)
        cls.init_aesthetics()
    
    @classmethod
    def init_aesthetics(cls):
        # Current League ID
        try:
            cls.current_league_id = cls.league_service.get_my_league() or None
        except Exception:
            cls.current_league_id = None

        # Current League Name
        try:
            cls.current_league_name = cls.league_service.get_my_league_name() or None
        except Exception:
            cls.current_league_name = None

        # Current League Owner status
        try:
            cls.is_league_owner = cls.league_service.get_league_owner_status() or False
        except Exception:
            cls.is_league_owner = False

        # Current League forfeit
        try:
            cls.league_forfeit = cls.league_service.get_league_forfeit() or None
        except Exception:
            cls.league_forfeit = None

        # Current Team ID
        try:
            cls.current_team_id = cls.team_service.get_my_team() or None
        except Exception:
            cls.current_team_id = None

        # Current Team Name
        try:
            cls.current_team_name = cls.team_service.get_my_team_name() or None
        except Exception:
            cls.current_team_name = None
    
    @classmethod
    def reset(cls):
        cls.user = None
        cls.current_league_id = None
        cls.current_league_name = None
        cls.is_league_owner = False
        cls.league_forfeit = None

        cls.auth_base = None
        cls.team_service = None
        cls.league_service = None
        cls.leaderboard_service = None