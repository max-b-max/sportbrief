"""
Package de configuration pour SportBrief
"""
from .api_config import (
    SPORTS_CONFIG,
    get_sport_config,
    get_api_key,
    get_api_url,
)

from .preferences import (
    get_preferences,
    reload_preferences,
    UserPreferences,
)

from .api_mapper import (
    get_api_mapper,
    get_sport_api_config,
    APIMapper,
)

from .id_resolver import (
    get_id_resolver,
    IDResolver,
)

from .season_helper import (
    get_current_season,
    format_season_display,
    CURRENT_BASKETBALL_SEASON,
    CURRENT_FOOTBALL_SEASON,
    CURRENT_RUGBY_SEASON,
    CURRENT_HANDBALL_SEASON,
    CURRENT_VOLLEYBALL_SEASON,
    CURRENT_MMA_SEASON,
)

from .season_fallback_helper import (
    get_best_season,
    get_previous_season,
    get_season_with_fallback,
)

from .current_season_resolver import (
    get_current_season_from_api,
    get_current_seasons_for_sport,
    clear_cache as clear_seasons_cache,
)

__all__ = [
    "SPORTS_CONFIG",
    "get_sport_config",
    "get_api_key",
    "get_api_url",
    "get_preferences",
    "reload_preferences",
    "UserPreferences",
    "get_api_mapper",
    "get_sport_api_config",
    "APIMapper",
    "get_id_resolver",
    "IDResolver",
    # Season helper
    "get_current_season",
    "format_season_display",
    "CURRENT_BASKETBALL_SEASON",
    "CURRENT_FOOTBALL_SEASON",
    "CURRENT_RUGBY_SEASON",
    "CURRENT_HANDBALL_SEASON",
    "CURRENT_VOLLEYBALL_SEASON",
    "CURRENT_MMA_SEASON",
]
