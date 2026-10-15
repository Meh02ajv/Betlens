from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class CompetitionOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    country: str
    type: str
    logo_url: str | None
    sport_code: str

    model_config = {"from_attributes": True}


class TeamOut(BaseModel):
    id: uuid.UUID
    name: str
    short_name: str
    slug: str
    country: str
    logo_url: str | None
    sport_code: str

    model_config = {"from_attributes": True}


class StandingOut(BaseModel):
    rank: int
    team_id: uuid.UUID
    team_name: str
    team_logo: str | None
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
    form: str


class MatchOut(BaseModel):
    id: uuid.UUID
    competition_id: uuid.UUID
    round: str
    kickoff_at: datetime
    status: str
    home_team_id: uuid.UUID
    home_team_name: str
    home_team_logo: str | None
    away_team_id: uuid.UUID
    away_team_name: str
    away_team_logo: str | None
    home_score: int | None
    away_score: int | None
    minute: int | None
    venue_name: str | None

    model_config = {"from_attributes": True}


class PlayerOut(BaseModel):
    id: uuid.UUID
    name: str
    position: str
    team_id: uuid.UUID
    team_name: str
    jersey_number: int | None
    nationality: str
    photo_url: str | None

    model_config = {"from_attributes": True}


class SearchResult(BaseModel):
    type: str  # team | player | competition | match
    id: uuid.UUID
    name: str
    subtitle: str | None
    logo_url: str | None