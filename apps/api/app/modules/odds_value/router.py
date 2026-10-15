from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.core.deps import CurrentUserId, DbSession, OptionalUserId
from app.db.models import (
    Bookmaker,
    Match,
    Odds,
    Prediction,
    UserBet,
    ValueOpportunity,
)

router = APIRouter()


@router.get("/matches/{match_id}/odds", response_model=list[dict])
async def get_match_odds(match_id: uuid.UUID, db: DbSession) -> list[dict]:
    match = await db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    result = await db.execute(
        select(Odds).where(Odds.match_id == match_id).order_by(Odds.market, Odds.captured_at.desc())
    )
    odds_list = result.scalars().all()

    out: list[dict[str, Any]] = []
    for o in odds_list:
        bm = await db.get(Bookmaker, o.bookmaker_id)
        implied_prob = round(1 / o.price_decimal, 4) if o.price_decimal > 0 else 0
        out.append({
            "id": str(o.id),
            "bookmaker": bm.name if bm else "Unknown",
            "market": o.market,
            "selection": o.selection,
            "price_decimal": o.price_decimal,
            "implied_probability": implied_prob,
            "captured_at": o.captured_at.isoformat(),
        })
    return out


@router.get("/value", response_model=list[dict])
async def get_value_opportunities(
    db: DbSession,
    user_id: CurrentUserId = None,  # type: ignore[assignment]
    competition: str | None = Query(None),
    min_edge: float = Query(0.03, ge=0.0, le=1.0),
    min_confidence: str | None = Query(None),
    limit: int = Query(20, le=100),
) -> list[dict]:
    result = await db.execute(
        select(ValueOpportunity)
        .where(ValueOpportunity.edge >= min_edge)
        .order_by(ValueOpportunity.edge.desc())
        .limit(limit)
    )
    vos = result.scalars().all()

    out = []
    for vo in vos:
        pred = await db.get(Prediction, vo.prediction_id)
        if not pred:
            continue
        if min_confidence and pred.confidence != min_confidence:
            continue
        match = await db.get(Match, pred.match_id)
        odds = await db.get(Odds, vo.odds_id)
        bm = await db.get(Bookmaker, odds.bookmaker_id) if odds else None

        out.append({
            "id": str(vo.id),
            "match_id": str(pred.match_id),
            "market": pred.market,
            "selection": pred.selection,
            "model_probability": vo.model_prob,
            "implied_probability": vo.implied_prob,
            "edge": vo.edge,
            "expected_value": vo.expected_value,
            "confidence": pred.confidence,
            "bookmaker": bm.name if bm else "Unknown",
            "price_decimal": odds.price_decimal if odds else None,
            "kickoff_at": match.kickoff_at.isoformat() if match else None,
        })
    return out


@router.post("/slips/analyze", response_model=dict)
async def analyze_slip(
    selections: list[dict],
    db: DbSession,
    user_id: CurrentUserId = None,  # type: ignore[assignment]
) -> dict:
    """
    Analyze an accumulator slip.
    Each selection: {prediction_id, market, selection, odds_decimal}
    """
    if not selections:
        raise HTTPException(status_code=400, detail="No selections provided")

    combined_prob = 1.0
    combined_odds = 1.0
    correlated_warning = False
    match_ids: set[str] = set()

    for sel in selections:
        prob = sel.get("probability", 0.5)
        odds = sel.get("odds_decimal", 2.0)
        match_id = sel.get("match_id")

        combined_prob *= prob
        combined_odds *= odds

        if match_id:
            if match_id in match_ids:
                correlated_warning = True
            match_ids.add(match_id)

    combined_prob = round(combined_prob, 6)
    combined_odds = round(combined_odds, 2)
    expected_value = round(combined_prob * (combined_odds - 1) - (1 - combined_prob), 4)

    if combined_prob >= 0.5:
        risk_label = "Low"
    elif combined_prob >= 0.25:
        risk_label = "Medium"
    elif combined_prob >= 0.1:
        risk_label = "High"
    else:
        risk_label = "Very High"

    return {
        "combined_probability": combined_prob,
        "combined_odds": combined_odds,
        "expected_value": expected_value,
        "risk_label": risk_label,
        "correlated_warning": correlated_warning,
        "disclaimer": "Estimates based on statistical models. No outcome is guaranteed.",
    }


# ── Bet tracker ───────────────────────────────────────────────────────────────

@router.get("/bets", response_model=list[dict])
async def get_bets(user_id: CurrentUserId, db: DbSession) -> list[dict]:
    result = await db.execute(
        select(UserBet).where(UserBet.user_id == user_id).order_by(UserBet.placed_at.desc())
    )
    bets = result.scalars().all()
    return [
        {
            "id": str(b.id),
            "market": b.market,
            "selection": b.selection,
            "stake": b.stake,
            "odds_decimal": b.odds_decimal,
            "status": b.status,
            "profit": b.profit,
            "placed_at": b.placed_at.isoformat(),
            "notes": b.notes,
        }
        for b in bets
    ]


@router.post("/bets", response_model=dict, status_code=201)
async def create_bet(bet_data: dict, user_id: CurrentUserId, db: DbSession) -> dict:
    bet = UserBet(
        user_id=user_id,
        market=bet_data.get("market", ""),
        selection=bet_data.get("selection", ""),
        stake=float(bet_data.get("stake", 0)),
        odds_decimal=float(bet_data.get("odds_decimal", 1.0)),
        status="pending",
        notes=bet_data.get("notes", ""),
    )
    db.add(bet)
    await db.flush()
    return {"id": str(bet.id), "message": "Bet logged successfully"}


@router.patch("/bets/{bet_id}", response_model=dict)
async def update_bet(bet_id: uuid.UUID, bet_data: dict, user_id: CurrentUserId, db: DbSession) -> dict:
    bet = await db.get(UserBet, bet_id)
    if not bet or bet.user_id != user_id:
        raise HTTPException(status_code=404, detail="Bet not found")

    if "status" in bet_data:
        bet.status = bet_data["status"]
        if bet_data["status"] == "won":
            bet.profit = round(bet.stake * (bet.odds_decimal - 1), 2)
        elif bet_data["status"] == "lost":
            bet.profit = -bet.stake
    if "notes" in bet_data:
        bet.notes = bet_data["notes"]

    await db.flush()
    return {"id": str(bet.id), "status": bet.status, "profit": bet.profit}


@router.delete("/bets/{bet_id}", status_code=200)
async def delete_bet(bet_id: uuid.UUID, user_id: CurrentUserId, db: DbSession) -> dict:
    bet = await db.get(UserBet, bet_id)
    if not bet or bet.user_id != user_id:
        raise HTTPException(status_code=404, detail="Bet not found")
    await db.delete(bet)
    return {"message": "Deleted"}


@router.get("/bets/stats", response_model=dict)
async def get_bet_stats(user_id: CurrentUserId, db: DbSession) -> dict:
    result = await db.execute(
        select(UserBet).where(UserBet.user_id == user_id, UserBet.status != "pending")
    )
    bets = result.scalars().all()

    if not bets:
        return {"total_bets": 0, "won": 0, "lost": 0, "total_profit": 0.0, "roi": 0.0, "hit_rate": 0.0}

    won = sum(1 for b in bets if b.status == "won")
    lost = sum(1 for b in bets if b.status == "lost")
    total_stake = sum(b.stake for b in bets)
    total_profit = sum(b.profit or 0 for b in bets)
    roi = round(total_profit / total_stake * 100, 2) if total_stake > 0 else 0.0
    hit_rate = round(won / len(bets) * 100, 2) if bets else 0.0

    return {
        "total_bets": len(bets),
        "won": won,
        "lost": lost,
        "total_stake": round(total_stake, 2),
        "total_profit": round(total_profit, 2),
        "roi": roi,
        "hit_rate": hit_rate,
    }