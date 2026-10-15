from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, date as date_type, datetime

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.core.deps import CurrentUserId, DbSession
from app.db.models import Match, Prediction, Team, User, UserFavorite, ValueOpportunity
from app.modules.users.schemas import (
    DashboardResponse,
    DashboardTeamItem,
    FavoriteItem,
    FavoritesResponse,
    UpdateProfileRequest,
    UserProfile,
)
from app.providers.provider_factory import (
    fetch_fixtures,
    fetch_nba_games,
    get_football_provider,
    get_nba_provider,
)

router = APIRouter()


@router.get("", response_model=UserProfile)
async def get_profile(user_id: CurrentUserId, db: DbSession) -> UserProfile:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile.model_validate(user)


@router.patch("", response_model=UserProfile)
async def update_profile(
    data: UpdateProfileRequest, user_id: CurrentUserId, db: DbSession
) -> UserProfile:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    await db.flush()
    return UserProfile.model_validate(user)


@router.delete("", status_code=200)
async def delete_account(user_id: CurrentUserId, db: DbSession) -> dict:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.deleted_at = datetime.now(UTC)
    await db.flush()
    return {"message": "Account deleted"}


@router.get("/export")
async def export_data(user_id: CurrentUserId, db: DbSession) -> dict:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "created_at": user.created_at.isoformat(),
        },
        "message": "Full data export would be emailed in production.",
    }


@router.get("/favorites", response_model=FavoritesResponse)
async def get_favorites(user_id: CurrentUserId, db: DbSession) -> FavoritesResponse:
    result = await db.execute(select(UserFavorite).where(UserFavorite.user_id == user_id))
    favs = result.scalars().all()
    return FavoritesResponse(
        favorites=[FavoriteItem(entity_type=f.entity_type, entity_id=f.entity_id) for f in favs]
    )


@router.put("/favorites", response_model=FavoritesResponse)
async def set_favorites(
    data: FavoritesResponse, user_id: CurrentUserId, db: DbSession
) -> FavoritesResponse:
    # Delete existing
    existing = await db.execute(select(UserFavorite).where(UserFavorite.user_id == user_id))
    for fav in existing.scalars().all():
        await db.delete(fav)

    # Add new
    for item in data.favorites:
        fav = UserFavorite(
            user_id=user_id,
            entity_type=item.entity_type,
            entity_id=item.entity_id,
        )
        db.add(fav)

    await db.flush()
    return data


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    user_id: CurrentUserId,
    db: DbSession,
    requested_date: str | None = Query(None, alias="date"),
) -> DashboardResponse:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get favorite teams
    fav_result = await db.execute(
        select(UserFavorite).where(
            UserFavorite.user_id == user_id,
            UserFavorite.entity_type == "team",
        )
    )
    fav_team_ids = [f.entity_id for f in fav_result.scalars().all()]

    your_teams: list[DashboardTeamItem] = []
    for team_id in fav_team_ids[:6]:
        team = await db.get(Team, team_id)
        if not team:
            continue

        # Next match
        next_match_result = await db.execute(
            select(Match)
            .where(
                Match.status == "scheduled",
                (Match.home_team_id == team_id) | (Match.away_team_id == team_id),
            )
            .order_by(Match.kickoff_at)
            .limit(1)
        )
        next_match = next_match_result.scalars().first()

        # Last result
        last_result_q = await db.execute(
            select(Match)
            .where(
                Match.status == "finished",
                (Match.home_team_id == team_id) | (Match.away_team_id == team_id),
            )
            .order_by(Match.kickoff_at.desc())
            .limit(1)
        )
        last_result = last_result_q.scalars().first()

        # Win probability for next match
        win_prob: float | None = None
        if next_match:
            pred_result = await db.execute(
                select(Prediction).where(
                    Prediction.match_id == next_match.id,
                    Prediction.market == "1x2",
                    Prediction.selection == ("home" if next_match.home_team_id == team_id else "away"),
                )
            )
            pred = pred_result.scalars().first()
            if pred:
                win_prob = pred.probability

        your_teams.append(
            DashboardTeamItem(
                team_id=team.id,
                team_name=team.name,
                team_logo=team.logo_url,
                next_match={
                    "id": str(next_match.id),
                    "kickoff_at": next_match.kickoff_at.isoformat(),
                    "status": next_match.status,
                } if next_match else None,
                last_result={
                    "id": str(last_result.id),
                    "home_score": last_result.home_score,
                    "away_score": last_result.away_score,
                } if last_result else None,
                win_probability=win_prob,
            )
        )

    # Today's matches
    try:
        target_date = date_type.fromisoformat(requested_date) if requested_date else datetime.now(UTC).date()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="date must use YYYY-MM-DD format") from exc

    today_start = datetime.combine(target_date, datetime.min.time(), tzinfo=UTC)
    today_end = today_start.replace(hour=23, minute=59, second=59)
    today_matches = []
    if get_football_provider() != "mock":
        competition_slugs = (
            "premier-league",
            "la-liga",
            "serie-a",
            "bundesliga",
            "ligue-1",
            "champions-league",
        )

        results = await asyncio.gather(
            *(fetch_fixtures(slug) for slug in competition_slugs),
            return_exceptions=True,
        )
        for rows in results:
            if isinstance(rows, Exception):
                continue
            for row in rows:
                kickoff = row.get("kickoff_at", "")
                if kickoff[:10] == target_date.isoformat():
                    today_matches.append(row)
        today_matches = today_matches[:20]

    if get_nba_provider() != "mock" and len(today_matches) < 20:
        nba_rows = await fetch_nba_games()
        today_matches.extend(
            row for row in nba_rows
            if row.get("kickoff_at", "")[:10] == target_date.isoformat()
        )
        today_matches = today_matches[:20]

    if not today_matches:
        today_result = await db.execute(
            select(Match)
            .where(Match.kickoff_at >= today_start, Match.kickoff_at <= today_end)
            .order_by(Match.kickoff_at)
            .limit(20)
        )
        for match in today_result.scalars().all():
            home_team = await db.get(Team, match.home_team_id)
            away_team = await db.get(Team, match.away_team_id)
            if not home_team or not away_team:
                continue
            today_matches.append({
                "id": str(match.id),
                "competition_id": str(match.competition_id),
                "round": match.round,
                "kickoff_at": match.kickoff_at.isoformat(),
                "status": match.status,
                "home_team_id": str(match.home_team_id),
                "home_team_name": home_team.name,
                "home_team_logo": home_team.logo_url,
                "away_team_id": str(match.away_team_id),
                "away_team_name": away_team.name,
                "away_team_logo": away_team.logo_url,
                "home_score": match.home_score,
                "away_score": match.away_score,
                "minute": match.minute,
                "venue_name": None,
            })

    # Value spotlight (top 3)
    value_result = await db.execute(
        select(ValueOpportunity).order_by(ValueOpportunity.edge.desc()).limit(3)
    )
    value_spotlight = [
        {
            "id": str(v.id),
            "edge": v.edge,
            "expected_value": v.expected_value,
            "model_prob": v.model_prob,
            "implied_prob": v.implied_prob,
        }
        for v in value_result.scalars().all()
    ]

    hour = datetime.now(UTC).hour
    greeting_time = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"

    return DashboardResponse(
        greeting=f"{greeting_time}, {user.name}!",
        your_teams=your_teams,
        today_matches=today_matches,
        top_probabilities=[],
        value_spotlight=value_spotlight,
    )