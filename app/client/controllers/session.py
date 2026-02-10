from datetime import datetime, timedelta
from packaging import version

from app.services.league_service import LeagueService
from app.services.leaderboard_service import LeaderboardService
from app.services.team_service import TeamService

class Session:
    '''
    Class responsible with storing all cached data for the application.
    '''
    VERSION = "1.2.0"

    # authenticated supabase session
    auth_base                               = None

    # username and user id
    user                                    = None
    user_id                                 = None

    '''
    cached system state info
    blocking defaults True: block everything if connection fails
    '''
    warning_message                         = None
    banner_message                          = None
    last_live_scores                        = None
    blocking_state                          = True
    min_version                             = VERSION

    # cached avatars
    avatar_cache                            = {}

    # cached league info
    current_league_id                       = None
    current_league_name                     = None
    league_forfeit                          = None
    leaguemates                             = None
    draft_order                             = None
    next_pick                               = None
    is_league_owner                         = False
    is_league_locked                        = False
    draft_complete                          = False

    # cached team info
    current_team_id                         = None
    current_team_name                       = None
    my_team_standings                       = None

    # cached leaderboard info
    player_scores                           = None
    leaguemate_standings                    = None
    global_stats                            = None

    # services locked and loaded
    team_service                            = None
    league_service                          = None
    leaderboard_service                     = None

    # refresh timers
    system_state_grabbed_at                 = None
    league_data_grabbed_at                  = None
    leaguemate_data_grabbed_at              = None

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
    def init_system_state(cls):
        # refresh timer logic - fixed at 5 mins
        current_time = datetime.now()

        if not (
            cls.system_state_grabbed_at is None
            or cls.system_state_grabbed_at <= current_time - timedelta(minutes=5)
        ):
            return cls.blocking_state
        # system state info
        try:
            system_state = cls.auth_base.get_system_state()
            cls.system_state_grabbed_at = datetime.now()

            cls.blocking_state = system_state["blocking"]
            cls.banner_message = system_state["banner_message"]
            cls.warning_message = system_state["warning_message"]
            cls.min_version = system_state["version"]

            client_version = version.parse(cls.VERSION.strip('"'))
            server_version = version.parse(cls.min_version.strip('"'))

            if server_version.release[1] > client_version.release[1]:
                cls.blocking_state = True
                cls.warning_message = f"Unsupported Version, please download the latest version ({server_version}) from the GitHub page: https://github.com/bfararjeh/sf6-fantasy-league/releases"

            cls.player_scores = cls.leaderboard_service.get_players()
            cls.global_stats = cls.leaderboard_service.get_global_stats()

            return cls.blocking_state

        except Exception as e:
            cls.blocking_state = True
            cls.banner_message = None
            cls.warning_message = f"CRITICAL ERROR: Unable to connect to database. Error {e}"
            return cls.blocking_state
    
    @classmethod
    def init_league_data(cls, force=False):
        if cls.init_system_state():
            return
        
        if not cls._should_refresh(cls.league_data_grabbed_at, force=force):
            return

        # league data
        try:
            league_data = cls.league_service.get_full_league_info() or None
            cls.league_data_grabbed_at = datetime.now()

            cls.current_league_id = league_data["league_id"] or None
            cls.current_league_name = league_data["league_name"] or None
            cls.league_forfeit = league_data["forfeit"] or None
            cls.is_league_owner = True if league_data["league_owner"] == cls.user_id else False
            cls.leaguemates = league_data["leaguemates"]
            cls.is_league_locked = league_data["locked"]

            try:
                cls.draft_order = league_data["draft_order"]
                cls.next_pick = league_data["next_pick"]
                cls.draft_complete = league_data["draft_complete"]
            except Exception:
                cls.draft_order = None
                cls.next_pick = None
                cls.draft_complete = False

        except Exception:
            cls.league_data_grabbed_at = None

            cls.current_league_id = None
            cls.current_league_name = None
            cls.league_forfeit = None
            cls.is_league_owner = False
            cls.leaguemates = None
            cls.is_league_locked = False

            cls.draft_order = None
            cls.next_pick = None
            cls.draft_complete = False
        
        # team data
        try:
            team_data = cls.team_service.get_full_team_info() or None

            cls.current_team_id = team_data["team_id"] or None
            cls.current_team_name = team_data["team_name"] or None
            cls.my_team_standings = {k: team_data[k] for k in ("players", "total_points")} or None

        except Exception:
            cls.current_team_id = None
            cls.current_team_name = None
            cls.my_team_standings = None

    @classmethod
    def init_leaderboards(cls, force=False):
        if cls.init_system_state():
            return

        if not cls._should_refresh(cls.leaguemate_data_grabbed_at, force=force):
            return

        try:
            cls.leaguemate_standings = cls.leaderboard_service.get_leaguemate_standings()
            cls.leaguemate_data_grabbed_at = datetime.now()
        except Exception:
            cls.leaguemate_standings = None
            cls.leaguemate_data_grabbed_at = None
    
    @classmethod
    def init_global_stats(cls, force=False):
        if cls.init_system_state():
            return
        
        try:
            if cls.global_stats == None or force == True:
                cls.global_stats = cls.leaderboard_service.get_global_stats()

        except:
            cls.global_stats = None


    @classmethod
    def init_avatar(cls, user_id):
        try:
            if user_id in cls.avatar_cache:
                return cls.avatar_cache[user_id]
            
            # fetch if not in cache
            avatar_bytes = cls.auth_base.get_avatar(user_id)

            cls.avatar_cache[user_id] = avatar_bytes
            return avatar_bytes

        except Exception:
            # on any error, cache None
            cls.avatar_cache[user_id] = None
            return None

    @classmethod
    def _should_refresh(cls, grabbed_at, force=False):
        now = datetime.now()

        if force or grabbed_at is None:
            return True
        
        if not bool(cls.is_league_locked) and bool(cls.current_league_id):
            seconds = 90
        elif bool(cls.is_league_locked) and not bool(cls.draft_complete):
            seconds = 30
        else:
            seconds = 900

        return grabbed_at <= now - timedelta(seconds=seconds)

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

        # cached avatars
        cls.avatar_cache = {}

        # cached league info
        cls.current_league_id = None
        cls.current_league_name = None
        cls.league_forfeit = None
        cls.is_league_owner = False
        cls.leaguemates = None
        cls.is_league_locked = False
        cls.draft_order = None
        cls.next_pick = None
        cls.draft_complete = False

        # cached team info
        cls.current_team_id = None
        cls.current_team_name = None
        cls.my_team_standings = None

        # cached leaderboard info
        cls.player_scores = None
        cls.leaguemate_standings = None
        cls.global_stats = None

        # services locked and loaded
        cls.team_service = None
        cls.league_service = None
        cls.leaderboard_service = None

        # refresh timers
        cls.system_state_grabbed_at = None
        cls.league_data_grabbed_at = None
        cls.leaguemate_data_grabbed_at = None
