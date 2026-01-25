from packaging import version

from app.services.app_store import AppStore
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
    last_live_scores = None
    min_version = VERSION

    # cached league info
    current_league_id = None
    current_league_name = None
    league_forfeit = None
    is_league_owner = False
    leaguemates = []
    draft_order = []
    next_pick = None
    draft_complete = False

    # cached team info
    current_team_id = None
    current_team_name = None
    my_team_data = []

    # cached leaderboard info
    favourite_players = []
    player_scores = []
    leaguemate_standings = []
    favourite_standings = []

    # services locked and loaded
    team_service = None
    league_service = None
    leaderboard_service = None

    @classmethod
    def init_system_state(cls):
        # system state info
        try:
            system_state = cls.auth_base.get_system_state()
            cls.player_scores = cls.leaderboard_service.get_players()
            cls.blocking_state = system_state["blocking"]
            cls.banner_message = system_state["banner_message"]
            cls.warning_message = system_state["warning_message"]
            cls.last_live_scores = system_state["last_live_scores"]
            cls.min_version = system_state["version"]

            client_version = version.parse(cls.VERSION.strip('"'))
            server_version = version.parse(cls.min_version.strip('"'))

            if server_version.release[1] > client_version.release[1]:
                cls.blocking_state = True
                cls.warning_message = f"Unsupported Version, please download the latest version ({server_version}) from the GitHub page: https://github.com/bfararjeh/sf6-fantasy-league/releases"

            return cls.blocking_state

        except Exception as e:
            cls.blocking_state = True
            cls.banner_message = None
            cls.warning_message = f"CRITICAL ERROR: Unable to connect to database. Error {e}"
            return cls.blocking_state

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
    
    @classmethod
    def init_aesthetics(cls):
        if cls.init_system_state():
            return

        # league data
        try:
            league_data = cls.league_service.get_full_league_info() or None

            cls.current_league_id = league_data["league_id"] or None
            cls.current_league_name = league_data["league_name"] or None
            cls.league_forfeit = league_data["forfeit"] or None
            cls.is_league_owner = True if league_data["league_owner"] == cls.user_id else False
            cls.leaguemates = league_data["leaguemates"]
            try:
                cls.draft_order = league_data["draft_order"]
                cls.next_pick = league_data["next_pick"]
                cls.draft_complete = league_data["draft_complete"]
            except Exception:
                cls.draft_order = []
                cls.next_pick = None
                cls.draft_complete = False

        except Exception:
            cls.current_league_id = None
            cls.current_league_name = None
            cls.league_forfeit = None
            cls.is_league_owner = False
            cls.leaguemates = []
            cls.draft_order = []
            cls.next_pick = None
            cls.draft_complete = False

        # team data
        try:
            team_data = cls.team_service.get_full_team_info() or None
            cls.current_team_id = team_data["team_id"] or None
            cls.current_team_name = team_data["team_name"] or None
            cls.my_team_standings = {k: team_data[k] for k in ("players", "total_points")} or None

        except Exception as e:
            cls.current_team_id = None
            cls.current_team_name = None
            cls.my_team_standings = None

    @classmethod
    def init_leaderboards(cls):
        try:
            cls.leaguemate_standings = cls.leaderboard_service.get_leaguemate_standings()
            cls.favourite_standings = cls.leaderboard_service.get_favourite_standings(cls.favourite_players) if cls.favourite_players else []
        except Exception:
            cls.leaguemate_standings = []
            cls.favourite_standings = []

    @classmethod
    def init_favourites(cls):
        # favourites
        try:
            favourites = AppStore._load_all().get("favourites")
            if isinstance(favourites, list):
                cls.favourite_players = favourites
        except Exception as e:
            pass

        try:
            cls.favourite_standings = cls.leaderboard_service.get_favourite_standings(cls.favourite_players) if cls.favourite_players else None
        except Exception as e:
            cls.favourite_standings = None

    @classmethod
    def reset(cls):
        # authenticated supabase session
        cls.auth_base = None

        # username and user id
        cls.user = None
        cls.user_id = None

        '''
        cached system state info
        blocking defaults True: block everything if connection fails
        '''
        cls.blocking_state = True
        cls.warning_message = None
        cls.banner_message = None
        cls.last_live_scores = None
        cls.min_version = cls.VERSION

        # cached league info
        cls.current_league_id = None
        cls.current_league_name = None
        cls.league_forfeit = None
        cls.is_league_owner = False
        cls.leaguemates = []
        cls.draft_order = []
        cls.next_pick = None
        cls.draft_complete = False

        # cached team info
        cls.current_team_id = None
        cls.current_team_name = None
        cls.my_team_standings = []

        # cached leaderboard info
        cls.favourite_players = []
        cls.player_scores = []
        cls.leaguemate_standings = []
        cls.favourite_standings = []

        # services locked and loaded
        cls.team_service = None
        cls.league_service = None
        cls.leaderboard_service = None