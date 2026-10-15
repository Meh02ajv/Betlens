from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Query
from sqlalchemy import or_, select

from app.core.deps import DbSession, OptionalUserId
from app.db.models import (
    Competition,
    Match,
    Player,
    Season,
    SeasonSimulation,
    Standing,
    Team,
    Venue,
)
from app.modules.sports_data.schemas import (
    CompetitionOut,
    MatchOut,
    PlayerOut,
    SearchResult,
    StandingOut,
    TeamOut,
)

router = APIRouter()


# ── Competitions ──────────────────────────────────────────────────────────────

@router.get("/competitions", response_model=list[CompetitionOut])
async def list_competitions(db: DbSession) -> list[CompetitionOut]:
    from app.db.models import Sport
    result = await db.execute(select(Competition).order_by(Competition.name))
    comps = result.scalars().all()
    out = []
    for c in comps:
        sport = await db.get(Sport, c.sport_id) if c.sport_id else None
        out.append(CompetitionOut(
            id=c.id, name=c.name, slug=c.slug, country=c.country,
            type=c.type, logo_url=c.logo_url,
            sport_code=sport.code if sport else "football",
        ))
    return out


@router.get("/competitions/{slug}", response_model=dict)
async def get_competition(slug: str, db: DbSession) -> dict:
    comp = await db.scalar(select(Competition).where(Competition.slug == slug))
    if not comp:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Competition not found")
    return {
        "id": str(comp.id),
        "name": comp.name,
        "slug": comp.slug,
        "country": comp.country,
        "type": comp.type,
        "logo_url": comp.logo_url,
    }


@router.get("/competitions/{slug}/standings", response_model=list[StandingOut])
async def get_standings(slug: str, db: DbSession) -> list[StandingOut]:
    comp = await db.scalar(select(Competition).where(Competition.slug == slug))
    if not comp:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Competition not found")

    result = await db.execute(
        select(Standing)
        .where(Standing.competition_id == comp.id)
        .order_by(Standing.rank)
    )
    standings = result.scalars().all()
    out = []
    for s in standings:
        team = await db.get(Team, s.team_id)
        out.append(StandingOut(
            rank=s.rank,
            team_id=s.team_id,
            team_name=team.name if team else "Unknown",
            team_logo=team.logo_url if team else None,
            played=s.played, won=s.won, drawn=s.drawn, lost=s.lost,
            goals_for=s.goals_for, goals_against=s.goals_against,
            goal_difference=s.goals_for - s.goals_against,
            points=s.points, form=s.form,
        ))
    return out


@router.get("/competitions/{slug}/fixtures", response_model=list[MatchOut])
async def get_fixtures(
    slug: str,
    db: DbSession,
    status: str | None = Query(None),
    limit: int = Query(20, le=100),
) -> list[MatchOut]:
    comp = await db.scalar(select(Competition).where(Competition.slug == slug))
    if not comp:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Competition not found")

    q = select(Match).where(Match.competition_id == comp.id).order_by(Match.kickoff_at).limit(limit)
    if status:
        q = q.where(Match.status == status)

    result = await db.execute(q)
    matches = result.scalars().all()
    return [await _match_out(m, db) for m in matches]


@router.get("/competitions/{slug}/outlook", response_model=list[dict])
async def get_outlook(slug: str, db: DbSession) -> list[dict]:
    comp = await db.scalar(select(Competition).where(Competition.slug == slug))
    if not comp:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Competition not found")

    result = await db.execute(
        select(SeasonSimulation).where(SeasonSimulation.competition_id == comp.id)
    )
    sims = result.scalars().all()
    out = []
    for s in sims:
        team = await db.get(Team, s.team_id)
        out.append({
            "team_id": str(s.team_id),
            "team_name": team.name if team else "Unknown",
            "team_logo": team.logo_url if team else None,
            "outcome_probabilities": s.outcome_probabilities,
        })
    return out


# ── Teams ─────────────────────────────────────────────────────────────────────

@router.get("/teams/{team_id}", response_model=dict)
async def get_team(team_id: uuid.UUID, db: DbSession) -> dict:
    team = await db.get(Team, team_id)
    if not team:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Team not found")
    return {
        "id": str(team.id),
        "name": team.name,
        "short_name": team.short_name,
        "slug": team.slug,
        "country": team.country,
        "logo_url": team.logo_url,
    }


@router.get("/teams/{team_id}/fixtures", response_model=list[MatchOut])
async def get_team_fixtures(
    team_id: uuid.UUID,
    db: DbSession,
    limit: int = Query(10, le=50),
) -> list[MatchOut]:
    result = await db.execute(
        select(Match)
        .where(or_(Match.home_team_id == team_id, Match.away_team_id == team_id))
        .order_by(Match.kickoff_at.desc())
        .limit(limit)
    )
    matches = result.scalars().all()
    return [await _match_out(m, db) for m in matches]


@router.get("/teams/{team_id}/squad", response_model=list[PlayerOut])
async def get_squad(team_id: uuid.UUID, db: DbSession) -> list[PlayerOut]:
    result = await db.execute(select(Player).where(Player.team_id == team_id))
    players = result.scalars().all()
    team = await db.get(Team, team_id)
    return [
        PlayerOut(
            id=p.id, name=p.name, position=p.position,
            team_id=team_id, team_name=team.name if team else "",
            jersey_number=p.jersey_number, nationality=p.nationality,
            photo_url=p.photo_url,
        )
        for p in players
    ]


# ── Matches ───────────────────────────────────────────────────────────────────

@router.get("/matches", response_model=list[MatchOut])
async def list_matches(
    db: DbSession,
    date: str | None = Query(None, description="YYYY-MM-DD"),
    competition: str | None = Query(None, description="competition slug"),
    team: uuid.UUID | None = Query(None),
    limit: int = Query(20, le=100),
) -> list[MatchOut]:
    q = select(Match).order_by(Match.kickoff_at).limit(limit)

    if date:
        try:
            d = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=UTC)
            q = q.where(Match.kickoff_at >= d, Match.kickoff_at < d.replace(hour=23, minute=59))
        except ValueError:
            pass

    if competition:
        comp = await db.scalar(select(Competition).where(Competition.slug == competition))
        if comp:
            q = q.where(Match.competition_id == comp.id)

    if team:
        q = q.where(or_(Match.home_team_id == team, Match.away_team_id == team))

    result = await db.execute(q)
    matches = result.scalars().all()
    return [await _match_out(m, db) for m in matches]


@router.get("/matches/{match_id}", response_model=dict)
async def get_match(match_id: uuid.UUID, db: DbSession) -> dict:
    match = await db.get(Match, match_id)
    if not match:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Match not found")
    out = await _match_out(match, db)
    return out.model_dump()


@router.get("/matches/{match_id}/lineups", response_model=list[dict])
async def get_lineups(match_id: uuid.UUID, db: DbSession) -> list[dict]:
    from app.db.models import Lineup
    result = await db.execute(select(Lineup).where(Lineup.match_id == match_id))
    lineups = result.scalars().all()
    return [
        {
            "team_id": str(lu.team_id),
            "formation": lu.formation,
            "is_confirmed": lu.is_confirmed,
            "starters": lu.starters,
            "bench": lu.bench,
        }
        for lu in lineups
    ]


@router.get("/matches/{match_id}/events", response_model=list[dict])
async def get_match_events(match_id: uuid.UUID, db: DbSession) -> list[dict]:
    from app.db.models import MatchEvent
    result = await db.execute(
        select(MatchEvent).where(MatchEvent.match_id == match_id).order_by(MatchEvent.minute)
    )
    events = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "minute": e.minute,
            "type": e.type,
            "team_id": str(e.team_id) if e.team_id else None,
            "player_id": str(e.player_id) if e.player_id else None,
            "detail": e.detail,
        }
        for e in events
    ]


# ── Players ───────────────────────────────────────────────────────────────────

@router.get("/players/{player_id}", response_model=dict)
async def get_player(player_id: uuid.UUID, db: DbSession) -> dict:
    player = await db.get(Player, player_id)
    if not player:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Player not found")
    team = await db.get(Team, player.team_id)
    return {
        "id": str(player.id),
        "name": player.name,
        "position": player.position,
        "team_id": str(player.team_id),
        "team_name": team.name if team else "",
        "jersey_number": player.jersey_number,
        "nationality": player.nationality,
        "photo_url": player.photo_url,
        "birth_date": player.birth_date.isoformat() if player.birth_date else None,
    }


# ── Search ────────────────────────────────────────────────────────────────────

@router.get("/search", response_model=list[SearchResult])
async def search(q: str = Query(min_length=2), db: DbSession = None) -> list[SearchResult]:  # type: ignore[assignment]
    results: list[SearchResult] = []
    pattern = f"%{q}%"

    # Teams
    team_result = await db.execute(
        select(Team).where(Team.name.ilike(pattern)).limit(5)
    )
    for team in team_result.scalars().all():
        results.append(SearchResult(
            type="team", id=team.id, name=team.name,
            subtitle=team.country, logo_url=team.logo_url,
        ))

    # Players
    player_result = await db.execute(
        select(Player).where(Player.name.ilike(pattern)).limit(5)
    )
    for player in player_result.scalars().all():
        team = await db.get(Team, player.team_id)
        results.append(SearchResult(
            type="player", id=player.id, name=player.name,
            subtitle=team.name if team else None, logo_url=player.photo_url,
        ))

    # Competitions
    comp_result = await db.execute(
        select(Competition).where(Competition.name.ilike(pattern)).limit(3)
    )
    for comp in comp_result.scalars().all():
        results.append(SearchResult(
            type="competition", id=comp.id, name=comp.name,
            subtitle=comp.country, logo_url=comp.logo_url,
        ))

    return results[:15]


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _match_out(m: Match, db: DbSession) -> MatchOut:  # type: ignore[valid-type]
    home_team = await db.get(Team, m.home_team_id)
    away_team = await db.get(Team, m.away_team_id)
    venue = await db.get(Venue, m.venue_id) if m.venue_id else None
    return MatchOut(
        id=m.id,
        competition_id=m.competition_id,
        round=m.round,
        kickoff_at=m.kickoff_at,
        status=m.status,
        home_team_id=m.home_team_id,
        home_team_name=home_team.name if home_team else "Unknown",
        home_team_logo=home_team.logo_url if home_team else None,
        away_team_id=m.away_team_id,
        away_team_name=away_team.name if away_team else "Unknown",
        away_team_logo=away_team.logo_url if away_team else None,
        home_score=m.home_score,
        away_score=m.away_score,
        minute=m.minute,
        venue_name=venue.name if venue else None,
    )