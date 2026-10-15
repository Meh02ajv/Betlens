"""
NBA Elo / Net Rating model for win probability and player props.
"""
from __future__ import annotations

import math
import random
from typing import Any


class NBAModel:
    """
    Margin-adjusted Elo model for NBA win probability.

    Win probability is derived from a logistic function of the adjusted
    rating difference. Player props use projected minutes × per-minute rates,
    adjusted for opponent defense and pace.
    """

    MODEL_VERSION = "nba-elo-2026.10.1"
    HOME_COURT_ADVANTAGE = 3.5  # points
    ELO_K = 20  # K-factor for Elo updates

    def _get_team_elo(self, team_id: str) -> float:
        rng = random.Random(hash(team_id) % (2**31))
        return rng.uniform(1350, 1750)

    def predict_match(self, match_id: str) -> dict[str, Any]:
        rng = random.Random(hash(match_id) % (2**31))
        home_id = str(rng.randint(1000, 9999))
        away_id = str(rng.randint(1000, 9999))

        home_elo = self._get_team_elo(home_id) + self.HOME_COURT_ADVANTAGE * 25
        away_elo = self._get_team_elo(away_id)

        elo_diff = home_elo - away_elo
        home_win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
        away_win_prob = 1 - home_win_prob

        # Expected spread (points)
        expected_spread = round(elo_diff / 25, 1)

        # Expected total (based on pace)
        expected_total = round(rng.uniform(210, 240), 1)

        confidence = "high" if abs(elo_diff) > 150 else "medium" if abs(elo_diff) > 75 else "low"

        return {
            "win_probability": {
                "home": round(home_win_prob, 4),
                "away": round(away_win_prob, 4),
            },
            "expected_spread": expected_spread,
            "expected_total": expected_total,
            "confidence": confidence,
            "model_version": self.MODEL_VERSION,
            "factors": [
                {
                    "label": "Elo rating advantage",
                    "direction": "up" if elo_diff > 0 else "down",
                    "impact": round(min(abs(elo_diff) / 400, 0.2), 3),
                },
                {
                    "label": "Home court advantage",
                    "direction": "up",
                    "impact": 0.04,
                },
            ],
        }

    def predict_player_props(
        self,
        player_id: str,
        match_id: str,
        projected_minutes: float = 32.0,
    ) -> dict[str, Any]:
        """Predict player prop lines using projected minutes × per-minute rates."""
        rng = random.Random(hash(player_id + match_id) % (2**31))

        # Per-minute rates (mock — in production from player_stats)
        pts_per_min = rng.uniform(0.4, 0.9)
        reb_per_min = rng.uniform(0.1, 0.4)
        ast_per_min = rng.uniform(0.05, 0.3)

        projected_pts = pts_per_min * projected_minutes
        projected_reb = reb_per_min * projected_minutes
        projected_ast = ast_per_min * projected_minutes

        def over_prob(projected: float, line: float, std_dev: float = 4.0) -> float:
            """Normal distribution over/under probability."""
            z = (line - projected) / std_dev
            return round(1 - 0.5 * (1 + math.erf(z / math.sqrt(2))), 4)

        return {
            "player_id": player_id,
            "match_id": match_id,
            "projected_minutes": projected_minutes,
            "points": {
                "projection": round(projected_pts, 1),
                "lines": [
                    {"line": round(projected_pts - 2.5, 1), "over": over_prob(projected_pts, projected_pts - 2.5)},
                    {"line": round(projected_pts, 1), "over": over_prob(projected_pts, projected_pts)},
                    {"line": round(projected_pts + 2.5, 1), "over": over_prob(projected_pts, projected_pts + 2.5)},
                ],
            },
            "rebounds": {
                "projection": round(projected_reb, 1),
                "lines": [
                    {"line": round(projected_reb, 1), "over": over_prob(projected_reb, projected_reb, 2.5)},
                ],
            },
            "assists": {
                "projection": round(projected_ast, 1),
                "lines": [
                    {"line": round(projected_ast, 1), "over": over_prob(projected_ast, projected_ast, 2.0)},
                ],
            },
            "model_version": self.MODEL_VERSION,
        }