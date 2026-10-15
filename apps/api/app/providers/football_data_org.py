"""
Football-Data.org provider (free tier: 10 req/min, major competitions).
Docs: https://www.football-data.org/documentation/quickstart
"""
from __future__ import annotations

import httpx
from typing import Any

BASE_URL = "https://api.football-data.org/v4"

COMPETITION_MAP = {
    "premier-league": "PL",
    "la-liga": "PD",
    "serie-a": "SA",
    "bundesliga": "BL1",
    "ligue-1": "FL1",
    "champions-league": "CL",
}


def _headers(api_key: str) -> dict[str, str]:
    return {"X-Auth-Token": api_key}


async def get_standings(slug: str, api_key: str) -> list[dict[str, Any]]:
    code = COMPETITION_MAP.get(slug)
    if not code:
        return []
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{BASE_URL}/competitions/{code}/standings", headers=_headers(api_key))
        r.raise_for_status()
        data = r.json()

    standings = []
    for table in data.get("standings", []):
        if table.get("type") == "TOTAL":
            for row in table.get("table", []):
                team = row.get("team", {})
                form = row.get("form") or ""
                form_clean = form.replace(",", "")[:5]
                standings.append({
                    "rank": row.get("position", 0),
                    "team_id": str(team.get("id", "")),
                    "team_name": team.get("name", ""),
                    "team_logo": team.get("crest", ""),
                    "played": row.get("playedGames", 0),
                    "won": row.get("won", 0),
                    "drawn": row.get("draw", 0),
                    "lost": row.get("lost", 0),
                    "goals_for": row.get("goalsFor", 0),
                    "goals_against": row.get("goalsAgainst", 0),
                    "goal_difference": row.get("goalDifference", 0),
                    "points": row.get("points", 0),
                    "form": form_clean,
                })
    return standings


async def get_fixtures(
    slug: str,
    api_key: str,
    status: str | None = None,
    matchday: int | None = None,
) -> list[dict[str, Any]]:
    code = COMPETITION_MAP.get(slug)
    if not code:
        return []
    params: dict[str, str] = {}
    if status:
        params["status"] = status.upper()
    if matchday is not None:
        params["matchday"] = str(matchday)

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{BASE_URL}/competitions/{code}/matches",
            headers=_headers(api_key),
            params=params,
        )
        r.raise_for_status()
        data = r.json()

    matches = []
    for m in data.get("matches", [])[:30]:
        home = m.get("homeTeam", {})
        away = m.get("awayTeam", {})
        score = m.get("score", {})
        full = score.get("fullTime", {})
        status_raw = m.get("status", "SCHEDULED")

        status_map = {
            "SCHEDULED": "scheduled", "TIMED": "scheduled",
            "IN_PLAY": "live", "PAUSED": "live",
            "FINISHED": "finished", "POSTPONED": "postponed",
            "CANCELLED": "cancelled",
        }

        matches.append({
            "id": str(m.get("id", "")),
            "competition_id": slug,
            "round": m.get("matchday", ""),
            "kickoff_at": m.get("utcDate", ""),
            "status": status_map.get(status_raw, "scheduled"),
            "home_team_id": str(home.get("id", "")),
            "home_team_name": home.get("name", ""),
            "home_team_logo": home.get("crest", ""),
            "away_team_id": str(away.get("id", "")),
            "away_team_name": away.get("name", ""),
            "away_team_logo": away.get("crest", ""),
            "home_score": full.get("home"),
            "away_score": full.get("away"),
            "minute": m.get("minute"),
            "venue_name": None,
        })
    return matches


async def get_teams(slug: str, api_key: str) -> list[dict[str, Any]]:
    code = COMPETITION_MAP.get(slug)
    if not code:
        return []
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{BASE_URL}/competitions/{code}/teams", headers=_headers(api_key))
        r.raise_for_status()
        data = r.json()

    teams = []
    for t in data.get("teams", []):
        teams.append({
            "id": str(t.get("id", "")),
            "name": t.get("name", ""),
            "short_name": t.get("shortName", ""),
            "slug": t.get("shortName", "").lower().replace(" ", "-"),
            "country": t.get("area", {}).get("name", ""),
            "logo_url": t.get("crest", ""),
        })
    return teams