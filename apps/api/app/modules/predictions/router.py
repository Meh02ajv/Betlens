from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.deps import DbSession, OptionalUserId
from app.db.models import Match, Player, Prediction, Team
from app.modules.predictions.schemas import (
    FactorOut,
    MatchPredictionOut,
    PlayerPredictionOut,
    PredictionMarkets,
)

router = APIRouter()


@router.get("/matches/{match_id}/predictions", response_model=MatchPredictionOut)
async def get_match_predictions(
    match_id: uuid.UUID,
    db: DbSession,
    user_id: OptionalUserId = None,
) -> MatchPredictionOut:
    match = await db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    result = await db.execute(
        select(Prediction).where(Prediction.match_id == match_id)
    )
    preds = result.scalars().all()

    if not preds:
        raise HTTPException(status_code=404, detail="No predictions available for this match")

    # Build markets dict
    markets = PredictionMarkets()
    factors: list[FactorOut] = []
    model_version = "football-dc-2026.10.1"
    confidence = "medium"
    generated_at = datetime.now(UTC)

    for p in preds:
        model_version = p.model_version
        confidence = p.confidence
        generated_at = p.generated_at
        if p.factors and not factors:
            factors = [FactorOut(**f) for f in p.factors]

        if p.market == "1x2":
            if p.selection == "home":
                markets.home = p.probability
            elif p.selection == "draw":
                markets.draw = p.probability
            elif p.selection == "away":
                markets.away = p.probability
        elif p.market == "totals":
            if markets.totals is None:
                markets.totals = []
            markets.totals.append({"line": 2.5, "over": p.probability, "under": round(1 - p.probability, 3)})
        elif p.market == "btts":
            if p.selection == "yes":
                markets.btts = {"yes": p.probability, "no": round(1 - p.probability, 3)}

    # Compute expected goals from 1x2 probabilities (simplified)
    home_xg = round((markets.home or 0.4) * 3.5, 2)
    away_xg = round((markets.away or 0.3) * 3.0, 2)

    return MatchPredictionOut(
        match_id=match_id,
        model_version=model_version,
        generated_at=generated_at,
        confidence=confidence,
        markets=markets,
        expected_goals={"home": home_xg, "away": away_xg},
        factors=factors,
        players=[],
    )


@router.get("/players/{player_id}/predictions", response_model=PlayerPredictionOut)
async def get_player_predictions(
    player_id: uuid.UUID,
    db: DbSession,
    match_id: uuid.UUID | None = None,
) -> PlayerPredictionOut:
    player = await db.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Mock player predictions based on position
    position = player.position or "CM"
    is_forward = position in ["ST", "LW", "RW", "CAM"]
    is_midfielder = position in ["CM", "CDM", "CAM"]

    scorer_prob = 0.35 if is_forward else (0.12 if is_midfielder else 0.04)
    assist_prob = 0.20 if is_forward else (0.18 if is_midfielder else 0.06)
    decisive_prob = round(1 - (1 - scorer_prob) * (1 - assist_prob), 3)
    carded_prob = 0.08 if position in ["CB", "CDM"] else 0.05

    return PlayerPredictionOut(
        player_id=player_id,
        match_id=match_id or uuid.uuid4(),
        anytime_scorer=scorer_prob,
        assist=assist_prob,
        decisive=decisive_prob,
        carded=carded_prob,
        confidence="medium",
        factors=[
            FactorOut(label="Recent xG form", direction="up", impact=0.04),
            FactorOut(label="Opponent defensive rating", direction="down", impact=0.02),
        ],
    )


@router.get("/model/performance", response_model=dict)
async def get_model_performance(db: DbSession) -> dict:
    from app.db.models import ModelVersion
    result = await db.execute(select(ModelVersion).where(ModelVersion.is_active == True))  # noqa: E712
    models = result.scalars().all()
    return {
        "models": [
            {
                "name": m.name,
                "sport": m.sport,
                "trained_at": m.trained_at.isoformat(),
                "metrics": m.metrics,
                "is_active": m.is_active,
            }
            for m in models
        ],
        "methodology": {
            "football": "Dixon-Coles Poisson model with LightGBM second stage and isotonic calibration",
            "basketball": "Margin-adjusted Elo with logistic win probability and negative binomial player props",
            "calibration": "Walk-forward backtest on prior seasons; isotonic regression calibration",
            "evaluation": "Log loss, Brier score, ranked probability score vs market baseline",
        },
        "disclaimer": "Estimates based on statistical models. No outcome is guaranteed.",
    }