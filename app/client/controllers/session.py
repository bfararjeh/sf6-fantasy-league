from datetime import datetime, timedelta
from packaging import version

from app.services.league_service import LeagueService
from app.services.leaderboard_service import LeaderboardService
from app.services.team_service import TeamService
from app.services.event_service import EventService


class Session:
    """
    Local cache connecting the frontend to backend services.
    All state is stored as class attributes and refreshed on demand.
    """
    VERSION = "1.2.0"

    @classmethod
    def _set_defaults(cls):
        # authenticated supabase session
        cls.auth_base               = None

        # user info
        cls.user                    = None
        cls.user_id                 = None

        # system state (blocking defaults True: block everything if connection fails)
        cls.warning_message         = None
        cls.banner_message          = None
        cls.last_live_scores        = None
        cls.blocking_state          = True
        cls.updated_at              = None
        cls.min_version             = cls.VERSION

        # avatars
        cls.avatar_cache            = {}

        # league info
        cls.current_league_id       = None
        cls.current_league_name     = None
        cls.league_forfeit          = None
        cls.leaguemates             = None
        cls.is_league_owner         = False
        cls.is_league_locked        = False

        # draft info
        cls.draft_order             = None
        cls.next_pick               = None
        cls.draft_complete          = False

        # team info
        cls.current_team_id         = None
        cls.current_team_name       = None
        cls.my_team_standings       = None
        cls.my_inactive_players     = None

        # leaderboard info
        cls.player_scores           = None
        cls.leaguemate_standings    = None
        cls.global_stats            = None

        # event info
        cls.event_data              = None
        cls.dist_data               = None

        # services
        cls.team_service            = None
        cls.league_service          = None
        cls.leaderboard_service     = None
        cls.event_service           = None

        # refresh timers
        cls.system_state_grabbed_at     = None
        cls.league_data_grabbed_at      = None
        cls.leaguemate_data_grabbed_at  = None

# Apply defaults on class definition — single source of truth
Session._set_defaults()

class Session(Session):
    # initialisers
    @classmethod
    def init_services(cls):
        if not cls.auth_base:
            raise RuntimeError("Cannot initialize services without auth_base.")

        cls.user    = cls.auth_base.get_my_username()
        cls.user_id = cls.auth_base.user_id

        cls.team_service        = TeamService(cls.auth_base)
        cls.league_service      = LeagueService(cls.auth_base)
        cls.leaderboard_service = LeaderboardService(cls.auth_base)
        cls.event_service       = EventService(cls.auth_base)

    @classmethod
    def init_system_state(cls):
        if not cls._should_refresh(cls.system_state_grabbed_at, interval_override=300):
            return cls.blocking_state

        try:
            system_state = cls.auth_base.get_system_state()
            cls.system_state_grabbed_at = datetime.now()

            cls.blocking_state  = system_state["blocking"]
            cls.banner_message  = system_state["banner_message"]
            cls.warning_message = system_state["warning_message"]
            cls.min_version     = system_state["version"]
            cls.updated_at      = system_state["updated_at"]

            client_version = version.parse(cls.VERSION.strip('"'))
            server_version = version.parse(cls.min_version.strip('"'))

            if server_version.release[1] > client_version.release[1]:
                cls.blocking_state  = True
                cls.warning_message = (
                    f"Unsupported Version, please download the latest version "
                    f"({server_version}) from the GitHub page: "
                    f"https://github.com/bfararjeh/sf6-fantasy-league/releases"
                )

            # global data - doesnt need to be grabbed more than once at startup
            cls.player_scores = cls.leaderboard_service.get_players()
            cls.global_stats  = cls.leaderboard_service.get_global_stats()
            cls.event_data    = cls.event_service.get_events()
            cls.dist_data     = cls.event_service.get_distributions()

            return cls.blocking_state

        except Exception as e:
            cls.blocking_state  = True
            cls.banner_message  = None
            cls.warning_message = f"CRITICAL ERROR: Unable to connect to database. Error {e}"
            return cls.blocking_state

    @classmethod
    def init_league_data(cls, force=False):
        if not cls._should_refresh(cls.league_data_grabbed_at, force=force):
            return
        if cls.init_system_state():
            return

        # league data
        try:
            league_data = cls.league_service.get_full_league_info()
            cls.league_data_grabbed_at = datetime.now()

            cls.current_league_id   = league_data.get("league_id")
            cls.current_league_name = league_data.get("league_name")
            cls.league_forfeit      = league_data.get("forfeit")
            cls.is_league_owner     = league_data.get("league_owner") == cls.user_id
            cls.leaguemates         = league_data.get("leaguemates")
            cls.is_league_locked    = league_data.get("locked", False)

            # only present if draft has begun
            cls.draft_order    = league_data.get("draft_order")
            cls.next_pick      = league_data.get("next_pick")
            cls.draft_complete = league_data.get("draft_complete", False)

        except Exception:
            cls.league_data_grabbed_at = None
            cls._apply_league_defaults()

        # team data
        try:
            team_data = cls.team_service.get_full_team_info()

            cls.current_team_id     = team_data.get("team_id")
            cls.current_team_name   = team_data.get("team_name")
            cls.my_team_standings   = {k: team_data[k] for k in ("players", "total_points")}
            cls.my_inactive_players = team_data.get("inactive_players")

        except Exception:
            cls._apply_team_defaults()

    @classmethod
    def init_leaderboards(cls, force=False):
        if not cls._should_refresh(cls.leaguemate_data_grabbed_at, force=force):
            return
        if cls.init_system_state():
            return

        try:
            cls.leaguemate_standings        = cls.leaderboard_service.get_leaguemate_standings()
            cls.leaguemate_data_grabbed_at  = datetime.now()
        except Exception:
            cls.leaguemate_standings        = None
            cls.leaguemate_data_grabbed_at  = None

    @classmethod
    def init_avatar(cls, user_id):
        if user_id in cls.avatar_cache:
            return cls.avatar_cache[user_id]
        try:
            avatar_bytes = cls.auth_base.get_avatar(user_id)
            cls.avatar_cache[user_id] = avatar_bytes
            return avatar_bytes
        except Exception:
            cls.avatar_cache[user_id] = None
            return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @classmethod
    def _apply_league_defaults(cls):
        cls.current_league_id   = None
        cls.current_league_name = None
        cls.league_forfeit      = None
        cls.is_league_owner     = False
        cls.leaguemates         = None
        cls.is_league_locked    = False
        cls.draft_order         = None
        cls.next_pick           = None
        cls.draft_complete      = False

    @classmethod
    def _apply_team_defaults(cls):
        cls.current_team_id     = None
        cls.current_team_name   = None
        cls.my_team_standings   = None
        cls.my_inactive_players = None

    @classmethod
    def _should_refresh(cls, grabbed_at, force=False, interval_override=None):
        now = datetime.now()

        if force or grabbed_at is None:
            return True

        if interval_override is not None:
            seconds = interval_override
        elif not bool(cls.is_league_locked) and bool(cls.current_league_id):
            seconds = 90
        elif bool(cls.is_league_locked) and not bool(cls.draft_complete):
            seconds = 30
        else:
            seconds = 900

        return grabbed_at <= now - timedelta(seconds=seconds)

    @classmethod
    def reset(cls):
        cls._set_defaults()