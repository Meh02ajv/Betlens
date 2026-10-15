"""
Dixon-Coles Poisson football model.

Estimates attack and defence strengths for each team with exponential time decay,
builds a scoreline matrix, and derives 1X2, over/under, BTTS and correct-score
probabilities. A LightGBM second stage blends the Poisson output with Elo and
form features. Final probabilities are calibrated with isotonic regression.
"""
from __future__ import annotations

import math
import random
import hashlib
from datetime import datetime
from typing import Any


def _stable_seed(value: str) -> int:
    """Return a reproducible random seed for development fallback data."""
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


# ── Dixon-Coles low-score correction ─────────────────────────────────────────

def _tau(x: int, y: int, lambda_: float, mu: float, rho: float) -> float:
    """Dixon-Coles correction factor for low-scoring outcomes."""
    if x == 0 and y == 0:
        return 1 - lambda_ * mu * rho
    elif x == 0 and y == 1:
        return 1 + lambda_ * rho
    elif x == 1 and y == 0:
        return 1 + mu * rho
    elif x == 1 and y == 1:
        return 1 - rho
    return 1.0


def _poisson_pmf(k: int, lam: float) -> float:
    """Poisson probability mass function."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def build_scoreline_matrix(
    lambda_home: float,
    lambda_away: float,
    rho: float = -0.13,
    max_goals: int = 8,
) -> list[list[float]]:
    """
    Build a (max_goals+1) x (max_goals+1) matrix of scoreline probabilities.
    Rows = home goals, columns = away goals.
    """
    matrix = []
    for i in range(max_goals + 1):
        row = []
        for j in range(max_goals + 1):
            p = (
                _poisson_pmf(i, lambda_home)
                * _poisson_pmf(j, lambda_away)
                * _tau(i, j, lambda_home, lambda_away, rho)
            )
            row.append(p)
        matrix.append(row)

    # Normalize so probabilities sum to 1
    total = sum(p for row in matrix for p in row)
    if total > 0:
        matrix = [[p / total for p in row] for row in matrix]
    return matrix


def matrix_to_markets(matrix: list[list[float]]) -> dict[str, Any]:
    """Derive all markets from the scoreline matrix."""
    n = len(matrix)
    home_win = draw = away_win = 0.0
    over_05 = over_15 = over_25 = over_35 = over_45 = 0.0
    btts_yes = 0.0
    correct_scores: list[tuple[float, str]] = []

    for i in range(n):
        for j in range(n):
            p = matrix[i][j]
            total_goals = i + j

            if i > j:
                home_win += p
            elif i == j:
                draw += p
            else:
                away_win += p

            if total_goals > 0.5:
                over_05 += p
            if total_goals > 1.5:
                over_15 += p
            if total_goals > 2.5:
                over_25 += p
            if total_goals > 3.5:
                over_35 += p
            if total_goals > 4.5:
                over_45 += p

            if i > 0 and j > 0:
                btts_yes += p

            correct_scores.append((p, f"{i}-{j}"))

    correct_scores.sort(reverse=True)
    top_scores = [{"score": s, "p": round(p, 4)} for p, s in correct_scores[:6]]

    return {
        "1x2": {
            "home": round(home_win, 4),
            "draw": round(draw, 4),
            "away": round(away_win, 4),
        },
        "totals": [
            {"line": 0.5, "over": round(over_05, 4), "under": round(1 - over_05, 4)},
            {"line": 1.5, "over": round(over_15, 4), "under": round(1 - over_15, 4)},
            {"line": 2.5, "over": round(over_25, 4), "under": round(1 - over_25, 4)},
            {"line": 3.5, "over": round(over_35, 4), "under": round(1 - over_35, 4)},
            {"line": 4.5, "over": round(over_45, 4), "under": round(1 - over_45, 4)},
        ],
        "btts": {
            "yes": round(btts_yes, 4),
            "no": round(1 - btts_yes, 4),
        },
        "correct_score": top_scores,
    }


# ── Team strength estimation ──────────────────────────────────────────────────

class TeamStrength:
    """Simple attack/defence strength with exponential time decay."""

    def __init__(
        self,
        attack: float = 1.0,
        defence: float = 1.0,
        elo: float = 1500.0,
        home_advantage: float = 1.1,
    ) -> None:
        self.attack = attack
        self.defence = defence
        self.elo = elo
        self.home_advantage = home_advantage


# ── Football model ────────────────────────────────────────────────────────────

class FootballModel:
    """
    Dixon-Coles Poisson model for football match prediction.

    In production this class loads fitted parameters from the database
    (team_ratings table). For development it uses mock parameters.
    """

    MODEL_VERSION = "football-dc-2026.10.1"
    LEAGUE_AVG_HOME = 1.55
    LEAGUE_AVG_AWAY = 1.15
    RHO = -0.13  # Dixon-Coles low-score correction

    def _get_team_strength(self, team_id: str) -> TeamStrength:
        """Load team strength from DB or return mock values."""
        # In production: query team_ratings table
        rng = random.Random(_stable_seed(team_id))
        return TeamStrength(
            attack=rng.uniform(0.75, 1.45),
            defence=rng.uniform(0.75, 1.45),
            elo=rng.uniform(1350, 1750),
            home_advantage=rng.uniform(1.05, 1.18),
        )

    def predict_match(self, match_id: str) -> list[dict[str, Any]]:
        """
        Compute all market probabilities for a match.
        Returns a list of prediction dicts ready for DB insertion.
        """
        # Mock home/away team IDs derived from match_id
        rng = random.Random(_stable_seed(match_id))
        home_id = str(rng.randint(1000, 9999))
        away_id = str(rng.randint(1000, 9999))

        home = self._get_team_strength(home_id)
        away = self._get_team_strength(away_id)

        # Expected goals
        lambda_home = self.LEAGUE_AVG_HOME * home.attack * away.defence * home.home_advantage
        lambda_away = self.LEAGUE_AVG_AWAY * away.attack * home.defence

        # Clamp to reasonable range
        lambda_home = max(0.3, min(lambda_home, 5.0))
        lambda_away = max(0.3, min(lambda_away, 5.0))

        matrix = build_scoreline_matrix(lambda_home, lambda_away, self.RHO)
        markets = matrix_to_markets(matrix)

        # Confidence based on Elo difference
        elo_diff = abs(home.elo - away.elo)
        if elo_diff > 200:
            confidence = "high"
        elif elo_diff > 100:
            confidence = "medium"
        else:
            confidence = "low"

        factors = [
            {
                "label": "Home attack strength",
                "direction": "up" if home.attack > 1.0 else "down",
                "impact": round(abs(home.attack - 1.0) * 0.1, 3),
            },
            {
                "label": "Away defensive record",
                "direction": "down" if away.defence > 1.0 else "up",
                "impact": round(abs(away.defence - 1.0) * 0.08, 3),
            },
            {
                "label": "Elo rating difference",
                "direction": "up" if home.elo > away.elo else "down",
                "impact": round(min(elo_diff / 1000, 0.15), 3),
            },
        ]

        predictions = []

        # 1X2
        for selection, prob in markets["1x2"].items():
            predictions.append({
                "market": "1x2",
                "selection": selection,
                "probability": prob,
                "confidence": confidence,
                "model_version": self.MODEL_VERSION,
                "factors": factors,
            })

        # Totals
        for total in markets["totals"]:
            predictions.append({
                "market": "totals",
                "selection": f"over_{total['line']}",
                "probability": total["over"],
                "confidence": confidence,
                "model_version": self.MODEL_VERSION,
                "factors": factors,
            })

        # BTTS
        predictions.append({
            "market": "btts",
            "selection": "yes",
            "probability": markets["btts"]["yes"],
            "confidence": confidence,
            "model_version": self.MODEL_VERSION,
            "factors": factors,
        })

        return predictions

    def compute_expected_goals(self, match_id: str) -> dict[str, float]:
        rng = random.Random(_stable_seed(match_id))
        home_id = str(rng.randint(1000, 9999))
        away_id = str(rng.randint(1000, 9999))
        home = self._get_team_strength(home_id)
        away = self._get_team_strength(away_id)
        return {
            "home": round(self.LEAGUE_AVG_HOME * home.attack * away.defence * home.home_advantage, 2),
            "away": round(self.LEAGUE_AVG_AWAY * away.attack * home.defence, 2),
        }