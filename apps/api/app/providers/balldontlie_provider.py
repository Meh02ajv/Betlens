"""
BallDontLie NBA provider (free tier).
Docs: https://www.balldontlie.io/api/v1
"""

from __future__ import annotations
from typing import Any
import httpx
from datetime import date

BASE_URL = "https://api.balldontlie.io/v1"


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": api_key}


async def get_teams(api_key: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{BASE_URL}/teams", headers=_headers(api_key), params={"per_page": 100}
        )
        r.raise_for_status()
        data = r.json()
    teams = []
    for t in data.get("data", []):
        teams.append(
            {
                "id": str(t.get("id", "")),
                "name": t.get("full_name", ""),
                "short_name": t.get("abbreviation", ""),
                "slug": t.get("full_name", "").lower().replace(" ", "-"),
                "city": t.get("city", ""),
                "conference": t.get("conference", ""),
                "division": t.get("division", ""),
                "logo_url": f"https://a.espncdn.com/i/teamlogos/nba/500/{t.get('abbreviation', '').lower()}.png",
            }
        )
    return teams


async def get_games(
    api_key: str, season: int | None = None, team_ids: list[int] | None = None
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"per_page": 25}
    if season is not None:
        params["seasons[]"] = season
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{BASE_URL}/games", headers=_headers(api_key), params=params
        )
        r.raise_for_status()
        data = r.json()

    games = []
    for g in data.get("data", []):
        home = g.get("home_team", {})
        away = g.get("visitor_team", {})
        status = g.get("status", "")
        if status == "Final":
            match_status = "finished"
        elif any(x in status for x in ["Qtr", "Half", "OT"]):
            match_status = "live"
        else:
            match_status = "scheduled"

        games.append(
            {
                "id": str(g.get("id", "")),
                "kickoff_at": g.get("date", "") + "T00:00:00Z",
                "status": match_status,
                "home_team_id": str(home.get("id", "")),
                "home_team_name": home.get("full_name", ""),
                "home_team_logo": f"https://a.espncdn.com/i/teamlogos/nba/500/{home.get('abbreviation', '').lower()}.png",
                "away_team_id": str(away.get("id", "")),
                "away_team_name": away.get("full_name", ""),
                "away_team_logo": f"https://a.espncdn.com/i/teamlogos/nba/500/{away.get('abbreviation', '').lower()}.png",
                "competition_id": "nba",
                "round": "",
                "home_score": g.get("home_team_score"),
                "away_score": g.get("visitor_team_score"),
                "minute": None,
                "venue_name": None,
                "period": g.get("period", 0),
                "time": g.get("time", ""),
            }
        )
    return games


async def get_players(
    api_key: str, search: str = "", per_page: int = 25
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"per_page": per_page}
    if search:
        params["search"] = search
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{BASE_URL}/players", headers=_headers(api_key), params=params
        )
        r.raise_for_status()
        data = r.json()
    players = []
    for p in data.get("data", []):
        team = p.get("team", {})
        players.append(
            {
                "id": str(p.get("id", "")),
                "name": f"{p.get('first_name', '')} {p.get('last_name', '')}".strip(),
                "position": p.get("position", ""),
                "team_id": str(team.get("id", "")),
                "team_name": team.get("full_name", ""),
                "jersey_number": p.get("jersey_number"),
                "country": p.get("country", ""),
            }
        )
    return players
