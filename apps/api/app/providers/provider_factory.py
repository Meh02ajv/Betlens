"""
Provider factory — returns the correct data provider based on environment config.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
from datetime import date

# Load .env file explicitly so os.environ has all keys
def _load_env() -> None:
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if not env_path.exists():
        env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value

_load_env()


def current_nba_season() -> int:
    """NBA seasons start around October and are named by the start year."""
    today = date.today()
    return today.year if today.month >= 10 else today.year - 1


def get_football_provider() -> str:
    return os.environ.get("FOOTBALL_PROVIDER", "mock").strip('"').strip("'")

def get_nba_provider() -> str:
    return os.environ.get("NBA_PROVIDER", "mock").strip('"').strip("'")

def get_odds_provider() -> str:
    return os.environ.get("ODDS_PROVIDER", "mock").strip('"').strip("'")

def get_football_api_key() -> str:
    return (
        os.environ.get("FOOTBALL_DATA_ORG_KEY", "").strip('"').strip("'")
        or os.environ.get("FOOTBALL_API_KEY", "").strip('"').strip("'")
    )

def get_nba_api_key() -> str:
    return os.environ.get("NBA_API_KEY", "").strip('"').strip("'")

def get_odds_api_key() -> str:
    return os.environ.get("ODDS_API_KEY", "").strip('"').strip("'")


async def fetch_standings(slug: str) -> list[dict[str, Any]]:
    provider = get_football_provider()
    if provider in ("football_data_org", "api_football"):
        from app.providers.football_data_org import get_standings
        try:
            return await get_standings(slug, get_football_api_key())
        except Exception as e:
            print(f"[Provider] Standings error: {e}")
    return []


async def fetch_fixtures(
    slug: str,
    status: str | None = None,
    matchday: int | None = None,
) -> list[dict[str, Any]]:
    provider = get_football_provider()
    if provider in ("football_data_org", "api_football"):
        from app.providers.football_data_org import get_fixtures
        try:
            return await get_fixtures(slug, get_football_api_key(), status, matchday)
        except Exception as e:
            print(f"[Provider] Fixtures error: {e}")
    return []


async def fetch_nba_games(season: int | None = None) -> list[dict[str, Any]]:
    season = season or current_nba_season()
    provider = get_nba_provider()
    if provider == "balldontlie":
        from app.providers.balldontlie_provider import get_games
        try:
            return await get_games(get_nba_api_key(), season)
        except Exception as e:
            print(f"[Provider] NBA games error: {e}")
    return []


async def fetch_nba_teams() -> list[dict[str, Any]]:
    provider = get_nba_provider()
    if provider == "balldontlie":
        from app.providers.balldontlie_provider import get_teams
        try:
            return await get_teams(get_nba_api_key())
        except Exception as e:
            print(f"[Provider] NBA teams error: {e}")
    return []


async def fetch_odds(slug: str) -> list[dict[str, Any]]:
    provider = get_odds_provider()
    if provider == "the_odds_api":
        from app.providers.odds_provider import get_odds
        try:
            return await get_odds(slug, get_odds_api_key())
        except Exception as e:
            print(f"[Provider] Odds error: {e}")
    return []


async def fetch_football_teams(slug: str) -> list[dict[str, Any]]:
    provider = get_football_provider()
    if provider in ("football_data_org", "api_football"):
        from app.providers.football_data_org import get_teams
        try:
            return await get_teams(slug, get_football_api_key())
        except Exception as e:
            print(f"[Provider] Teams error: {e}")
    return []