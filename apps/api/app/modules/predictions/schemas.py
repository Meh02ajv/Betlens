from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class FactorOut(BaseModel):
    label: str
    direction: str  # up | down
    impact: float


class PredictionMarkets(BaseModel):
    home: float | None = None
    draw: float | None = None
    away: float | None = None
    totals: list[dict[str, Any]] | None = None
    btts: dict[str, float] | None = None
    correct_score: list[dict[str, Any]] | None = None
    cards: dict[str, float] | None = None


class MatchPredictionOut(BaseModel):
    match_id: uuid.UUID
    model_version: str
    generated_at: datetime
    confidence: str
    markets: PredictionMarkets
    expected_goals: dict[str, float] | None
    factors: list[FactorOut]
    players: list[dict[str, Any]]


class PlayerPredictionOut(BaseModel):
    player_id: uuid.UUID
    match_id: uuid.UUID
    anytime_scorer: float
    assist: float
    decisive: float
    carded: float
    confidence: str
    factors: list[FactorOut]