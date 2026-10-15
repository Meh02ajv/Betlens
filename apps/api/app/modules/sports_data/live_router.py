from __future__ import annotations
from typing import Any
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from app.core.deps import DbSession
from app.db.models import Competition, Match, Standing, Team
from app.providers.provider_factory import (
    fetch_fixtures, fetch_nba_games, fetch_nba_teams,
    fetch_odds, fetch_standings, get_football_provider,
    get_nba_provider, get_odds_provider,
)

router = APIRouter()


@router.get("/live/competitions/{slug}/standings", response_model=list[dict])
async def get_live_standings(slug: str, db: DbSession) -> list[dict]:
    provider = get_football_provider()
    if provider != "mock":
        data = await fetch_standings(slug)
        if data:
            return data
    # Fall back to DB
    comp = await db.scalar(select(Competition).where(Competition.slug == slug))
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    result = await db.execute(select(Standing).where(Standing.competition_id == comp.id).order_by(Standing.rank))
    standings = result.scalars().all()
    out = []
    for s in standings:
        team = await db.get(Team, s.team_id)
        out.append({
            "rank": s.rank, "team_id": str(s.team_id),
            "team_name": team.name if team else "Unknown",
            "team_logo": team.logo_url if team else None,
            "played": s.played, "won": s.won, "drawn": s.drawn, "lost": s.lost,
            "goals_for": s.goals_for, "goals_against": s.goals_against,
            "goal_difference": s.goals_for - s.goals_against,
            "points": s.points, "form": s.form,
        })
    return out


@router.get("/live/competitions/{slug}/fixtures", response_model=list[dict])
async def get_live_fixtures(
    slug: str,
    db: DbSession,
    status: str | None = Query(None),
    matchday: int | None = Query(None, ge=1, le=60),
) -> list[dict]:
    provider = get_football_provider()
    if provider != "mock":
        data = await fetch_fixtures(slug, status, matchday)
        if data:
            return data
    comp = await db.scalar(select(Competition).where(Competition.slug == slug))
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    q = select(Match).where(Match.competition_id == comp.id).order_by(Match.kickoff_at).limit(30)
    if status:
        q = q.where(Match.status == status)
    result = await db.execute(q)
    matches = result.scalars().all()
    out = []
    for m in matches:
        home = await db.get(Team, m.home_team_id)
        away = await db.get(Team, m.away_team_id)
        out.append({
            "id": str(m.id), "competition_id": str(m.competition_id),
            "round": m.round, "kickoff_at": m.kickoff_at.isoformat(),
            "status": m.status,
            "home_team_id": str(m.home_team_id),
            "home_team_name": home.name if home else "Unknown",
            "home_team_logo": home.logo_url if home else None,
            "away_team_id": str(m.away_team_id),
            "away_team_name": away.name if away else "Unknown",
            "away_team_logo": away.logo_url if away else None,
            "home_score": m.home_score, "away_score": m.away_score,
            "minute": m.minute, "venue_name": None,
        })
    return out


@router.get("/live/nba/games", response_model=list[dict])
async def get_live_nba_games(db: DbSession, season: int | None = Query(None)) -> list[dict]:
    provider = get_nba_provider()
    if provider != "mock":
        data = await fetch_nba_games(season)
        if data:
            return data
    return []


@router.get("/live/nba/teams", response_model=list[dict])
async def get_live_nba_teams(db: DbSession) -> list[dict]:
    provider = get_nba_provider()
    if provider != "mock":
        data = await fetch_nba_teams()
        if data:
            return data
    return []


@router.get("/live/odds/{slug}", response_model=list[dict])
async def get_live_odds(slug: str, db: DbSession) -> list[dict]:
    provider = get_odds_provider()
    if provider != "mock":
        return await fetch_odds(slug)
    return []


@router.get("/live/status", response_model=dict)
async def get_provider_status() -> dict:
    return {
        "football_provider": get_football_provider(),
        "nba_provider": get_nba_provider(),
        "odds_provider": get_odds_provider(),
        "status": "live" if get_football_provider() != "mock" else "mock",
    }