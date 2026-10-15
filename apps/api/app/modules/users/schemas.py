from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserProfile(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str
    avatar_url: str | None
    role: str
    plan: str
    locale: str
    timezone: str
    odds_format: str
    onboarding_completed: bool
    email_verified_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    avatar_url: str | None = None
    locale: str | None = None
    timezone: str | None = None
    odds_format: str | None = None


class FavoriteItem(BaseModel):
    entity_type: str  # team | competition | player
    entity_id: uuid.UUID


class FavoritesResponse(BaseModel):
    favorites: list[FavoriteItem]


class DashboardTeamItem(BaseModel):
    team_id: uuid.UUID
    team_name: str
    team_logo: str | None
    next_match: dict | None
    last_result: dict | None
    win_probability: float | None


class DashboardResponse(BaseModel):
    greeting: str
    your_teams: list[DashboardTeamItem]
    today_matches: list[dict]
    top_probabilities: list[dict]
    value_spotlight: list[dict]