from datetime import datetime, timedelta
from packaging import version

from app.services.league_service import LeagueService
from app.services.leaderboard_service import LeaderboardService
from app.services.team_service import TeamService
from app.services.event_service import EventService
from app.services.trade_service import TradeService


class Session:
    """
    Local cache connecting the frontend to backend services.
    All state is stored as class attributes and refreshed on demand.
    """
    VERSION = "1.3.0"
    SEASON = 13

    _on_block: callable = None

    @classmethod
    def _trigger_block(cls):
        if cls._on_block:
            cls._on_block()

    @classmethod
    def _set_defaults(cls):
        # authenticated supabase session
        cls._on_block: callable = None
        cls.auth_base               = None

        # user info
        cls.user                    = None
        cls.user_id                 = None

        # system state
        cls.blocking_state          = True
        cls.warning_message         = None
        cls.banner_message          = None
        cls.updated_at              = None
        cls.min_version             = cls.VERSION

        # avatars
        cls.avatar_cache            = {}

        # raw data stores
        cls.league_data             = None
        cls.team_data               = None
        cls.leaguemate_standings    = None
        cls.player_scores           = None
        cls.global_stats            = None
        cls.event_data              = None
        cls.qualified_data          = None

        cls.trade_windows           = None
        cls.trade_history           = None
        cls.trade_requests          = None
        cls.trade_players           = None

        # services
        cls.team_service            = None
        cls.league_service          = None
        cls.leaderboard_service     = None
        cls.event_service           = None
        cls.trade_service           = None

        # refresh timers
        cls.league_data_grabbed_at      = None
        cls.leaguemate_data_grabbed_at  = None
        cls.trade_data_grabbed_at       = None
        cls.system_state_grabbed_at     = None

Session._set_defaults()


class Session(Session):

    # ------------------------------------------------------------------
    # Initialisers
    # ------------------------------------------------------------------

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
        cls.trade_service       = TradeService(cls.auth_base)

    @classmethod
    def init_system_state(cls):
        if cls.system_state_grabbed_at is not None:
            if datetime.now() - cls.system_state_grabbed_at < timedelta(seconds=5):
                return cls.blocking_state
        try:
            system_state            = cls.auth_base.get_system_state()
            cls.system_state_grabbed_at = datetime.now()
            cls.blocking_state      = system_state["blocking"]
            cls.banner_message      = system_state["banner_message"]
            cls.warning_message     = system_state["warning_message"]
            cls.min_version         = system_state["version"]
            cls.updated_at          = system_state["updated_at"]

            client_version = version.parse(cls.VERSION.strip('"'))
            server_version = version.parse(cls.min_version.strip('"'))

            if server_version.release[1] > client_version.release[1]:
                cls.blocking_state  = True
                cls.warning_message = (
                    f"Unsupported Version, please download the latest version "
                    f"({server_version}) from the GitHub page: "
                    f"https://github.com/bfararjeh/sf6-fantasy-league/releases"
                )
            return cls.blocking_state

        except Exception as e:
            cls.blocking_state  = True
            cls.warning_message = f"ERROR: Unable to connect to database: {e}"
            return cls.blocking_state

    @classmethod
    def init_league_data(cls, force=False):
        if cls.init_system_state():
            cls._trigger_block()
            return
        if not cls._should_refresh(cls.league_data_grabbed_at, force=force):
            return

        try:
            cls.league_data             = cls.league_service.get_full_league_info()
            cls.league_data_grabbed_at  = datetime.now()
        except Exception:
            cls.league_data             = None
            cls.league_data_grabbed_at  = None

        try:
            cls.team_data = cls.team_service.get_full_team_info()
        except Exception:
            cls.team_data = None

    @classmethod
    def init_leaderboards(cls, force=False):
        if cls.init_system_state():
            cls._trigger_block()
            return
        if not cls._should_refresh(cls.leaguemate_data_grabbed_at, force=force):
            return

        try:
            cls.leaguemate_standings        = cls.leaderboard_service.get_leaguemate_standings()
            cls.leaguemate_data_grabbed_at  = datetime.now()
        except Exception:
            cls.leaguemate_standings        = None
            cls.leaguemate_data_grabbed_at  = None

    @classmethod
    def init_player_scores(cls):
        if cls.init_system_state():
            cls._trigger_block()
            return
        if cls.player_scores is not None:
            return

        try:
            cls.player_scores = cls.leaderboard_service.get_players()
        except Exception:
            cls.player_scores = None

    @classmethod
    def init_global_stats(cls):
        if cls.init_system_state():
            cls._trigger_block()
            return
        if cls.global_stats is not None:
            return

        try:
            cls.global_stats = cls.leaderboard_service.get_global_stats()
        except Exception:
            cls.global_stats = None

    @classmethod
    def init_event_data(cls):
        if cls.init_system_state():
            cls._trigger_block()
            return
        if cls.event_data is not None:
            return

        try:
            cls.event_data = cls.event_service.get_events()
        except Exception:
            cls.event_data = None

    @classmethod
    def init_qualified_data(cls):
        if cls.init_system_state():
            cls._trigger_block()
            return
        if cls.qualified_data is not None:
            return

        try:
            cls.qualified_data = cls.event_service.get_qualified()
        except Exception:
            cls.qualified_data = None

    @classmethod
    def init_trade_data(cls, force=False):
        if cls.init_system_state():
            cls._trigger_block()
            return
        if not cls._should_refresh(cls.trade_data_grabbed_at, force=force):
            return
        
        try:
            cls.trade_windows = cls.trade_service.get_trade_windows()
            cls.trade_history = cls.trade_service.get_trade_history()
            cls.trade_requests = cls.trade_service.get_open_requests(cls.user_id)
            cls.trade_players = cls.trade_service.get_pool_players()
        except Exception:
            cls.trade_windows = None
            cls.trade_history = None
            cls.trade_requests = None
            cls.trade_players = None

    # ------------------------------------------------------------------
    # Images
    # ------------------------------------------------------------------

    @classmethod
    def get_image(cls, image_type: str, key: str) -> bytes:
        """
        Full image pipeline:
        1. Check baked-in assets (players only)
        2. Check local disk cache + validate ETag
        3. Fetch from API if stale or missing
        4. Fall back to placeholder
        """
        from app.client.controllers.image_cache import ImageCache

        # 1. baked-in
        baked = ImageCache.get_baked(image_type, key)
        if baked:
            return baked

        # 2. disk cache
        cached = ImageCache.get_cached(image_type, key)
        cached_etag = ImageCache.get_etag(image_type, key)

        if cached and cached_etag:
            filename = cls._image_filename(image_type, key)
            remote_etag = cls.auth_base.get_image_etag(image_type, filename)
            if remote_etag == cached_etag:
                return cached

        # 3. fetch from API
        filename = cls._image_filename(image_type, key)
        data, etag = cls.auth_base.get_image(image_type, filename)
        if data:
            ImageCache.store(image_type, key, data, etag or "")
            return data

        # 4. placeholder
        return ImageCache.get_placeholder(image_type) or b""

    @classmethod
    def _image_filename(cls, image_type: str, key: str) -> str:
        if image_type == "avatars":
            return f"{key}.webp"
        return key.replace(" ", "_") + ".webp"

    @classmethod
    def init_avatar(cls, user_id: str) -> bytes:
        """Memory-cached wrapper for avatars since they're accessed repeatedly."""
        user_id = str(user_id)
        if user_id in cls.avatar_cache:
            return cls.avatar_cache[user_id]
        result = cls.get_image("avatars", user_id)
        cls.avatar_cache[user_id] = result
        return result

    @classmethod
    def get_pixmap(cls, image_type: str, key: str):
        from PyQt6.QtGui import QPixmap
        pixmap = QPixmap()
        data = cls.init_avatar(key) if image_type == "avatars" else cls.get_image(image_type, key)
        if data:
            pixmap.loadFromData(data)
        return pixmap


    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @classmethod
    def _should_refresh(cls, grabbed_at, force=False):
        if force or grabbed_at is None:
            return True
        seconds = cls.get_refresh_interval()
        return grabbed_at <= datetime.now() - timedelta(seconds=seconds)

    @classmethod
    def get_refresh_interval(cls) -> int:
        league = cls.league_data or {}
        if league.get("locked") and not league.get("draft_complete"):
            return 5
        elif league.get("league_id"):
            return 90
        else:
            return 900

    @classmethod
    def reset(cls):
        cls._set_defaults()
