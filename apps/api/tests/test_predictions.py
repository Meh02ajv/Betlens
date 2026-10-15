"""
Unit tests for the probability engine.
Tests use known inputs and verify mathematical correctness.
"""
from __future__ import annotations

import math

import pytest

from app.ml.models.football import (
    FootballModel,
    TeamStrength,
    _stable_seed,
    _poisson_pmf,
    _tau,
    build_scoreline_matrix,
    matrix_to_markets,
)


class TestStableSeed:
    def test_seed_is_reproducible(self) -> None:
        assert _stable_seed("match-123") == _stable_seed("match-123")
        assert _stable_seed("match-123") != _stable_seed("match-456")
from app.ml.models.nba import NBAModel


# ── Poisson helpers ───────────────────────────────────────────────────────────

class TestPoissonPMF:
    def test_zero_lambda(self) -> None:
        assert _poisson_pmf(0, 0) == 1.0
        assert _poisson_pmf(1, 0) == 0.0

    def test_known_values(self) -> None:
        # P(X=0 | λ=1.5) = e^-1.5 ≈ 0.2231
        assert abs(_poisson_pmf(0, 1.5) - math.exp(-1.5)) < 1e-9
        # P(X=1 | λ=1.5) = 1.5 * e^-1.5 ≈ 0.3347
        assert abs(_poisson_pmf(1, 1.5) - 1.5 * math.exp(-1.5)) < 1e-9

    def test_non_negative(self) -> None:
        for k in range(10):
            assert _poisson_pmf(k, 2.0) >= 0


class TestTau:
    def test_00_increases_probability_with_negative_rho(self) -> None:
        # With rho < 0, tau(0,0) > 1: Dixon-Coles increases the 0-0 probability
        # because negative rho means 0-0 is more common than Poisson predicts.
        result = _tau(0, 0, 1.5, 1.2, -0.13)
        assert result > 1.0

    def test_00_reduces_probability_with_positive_rho(self) -> None:
        # With rho > 0, tau(0,0) < 1
        result = _tau(0, 0, 1.5, 1.2, 0.13)
        assert result < 1.0

    def test_high_scores_unchanged(self) -> None:
        assert _tau(3, 2, 1.5, 1.2, -0.13) == 1.0
        assert _tau(5, 0, 1.5, 1.2, -0.13) == 1.0


# ── Scoreline matrix ──────────────────────────────────────────────────────────

class TestScorelineMatrix:
    def test_probabilities_sum_to_one(self) -> None:
        matrix = build_scoreline_matrix(1.5, 1.2)
        total = sum(p for row in matrix for p in row)
        assert abs(total - 1.0) < 1e-6

    def test_all_non_negative(self) -> None:
        matrix = build_scoreline_matrix(1.5, 1.2)
        for row in matrix:
            for p in row:
                assert p >= 0

    def test_higher_lambda_increases_goals(self) -> None:
        matrix_low = build_scoreline_matrix(0.5, 0.5)
        matrix_high = build_scoreline_matrix(3.0, 3.0)
        # High lambda should have more probability mass in high-scoring cells
        low_high_score = sum(matrix_low[i][j] for i in range(4, 9) for j in range(4, 9))
        high_high_score = sum(matrix_high[i][j] for i in range(4, 9) for j in range(4, 9))
        assert high_high_score > low_high_score


# ── Market derivation ─────────────────────────────────────────────────────────

class TestMatrixToMarkets:
    def setup_method(self) -> None:
        self.matrix = build_scoreline_matrix(1.72, 1.05)
        self.markets = matrix_to_markets(self.matrix)

    def test_1x2_sums_to_one(self) -> None:
        m = self.markets["1x2"]
        total = m["home"] + m["draw"] + m["away"]
        assert abs(total - 1.0) < 1e-4

    def test_btts_sums_to_one(self) -> None:
        btts = self.markets["btts"]
        assert abs(btts["yes"] + btts["no"] - 1.0) < 1e-4

    def test_totals_over_under_sum_to_one(self) -> None:
        for total in self.markets["totals"]:
            assert abs(total["over"] + total["under"] - 1.0) < 1e-4

    def test_over_25_monotone_with_lambda(self) -> None:
        """Higher expected goals → higher over 2.5 probability."""
        m_low = matrix_to_markets(build_scoreline_matrix(0.8, 0.7))
        m_high = matrix_to_markets(build_scoreline_matrix(2.5, 2.0))
        over_low = next(t["over"] for t in m_low["totals"] if t["line"] == 2.5)
        over_high = next(t["over"] for t in m_high["totals"] if t["line"] == 2.5)
        assert over_high > over_low

    def test_home_favored_when_high_attack(self) -> None:
        """Strong home attack → home win probability > away."""
        matrix = build_scoreline_matrix(3.0, 0.5)
        markets = matrix_to_markets(matrix)
        assert markets["1x2"]["home"] > markets["1x2"]["away"]

    def test_correct_score_top_entries(self) -> None:
        scores = self.markets["correct_score"]
        assert len(scores) > 0
        # Probabilities should be in descending order
        probs = [s["p"] for s in scores]
        assert probs == sorted(probs, reverse=True)

    def test_all_probabilities_in_range(self) -> None:
        m = self.markets["1x2"]
        for v in m.values():
            assert 0.0 <= v <= 1.0


# ── Football model ────────────────────────────────────────────────────────────

class TestFootballModel:
    def setup_method(self) -> None:
        self.model = FootballModel()

    def test_predict_match_returns_predictions(self) -> None:
        preds = self.model.predict_match("test-match-id-123")
        assert len(preds) > 0

    def test_all_markets_present(self) -> None:
        preds = self.model.predict_match("test-match-id-456")
        markets = {p["market"] for p in preds}
        assert "1x2" in markets
        assert "totals" in markets
        assert "btts" in markets

    def test_1x2_probabilities_sum_to_one(self) -> None:
        preds = self.model.predict_match("test-match-id-789")
        home = next(p["probability"] for p in preds if p["market"] == "1x2" and p["selection"] == "home")
        draw = next(p["probability"] for p in preds if p["market"] == "1x2" and p["selection"] == "draw")
        away = next(p["probability"] for p in preds if p["market"] == "1x2" and p["selection"] == "away")
        assert abs(home + draw + away - 1.0) < 1e-3

    def test_probabilities_in_valid_range(self) -> None:
        preds = self.model.predict_match("test-match-id-abc")
        for p in preds:
            assert 0.0 <= p["probability"] <= 1.0, f"Invalid probability: {p}"

    def test_confidence_is_valid(self) -> None:
        preds = self.model.predict_match("test-match-id-def")
        valid_confidences = {"low", "medium", "high"}
        for p in preds:
            assert p["confidence"] in valid_confidences

    def test_model_version_present(self) -> None:
        preds = self.model.predict_match("test-match-id-ghi")
        for p in preds:
            assert p["model_version"] == FootballModel.MODEL_VERSION

    def test_factors_present(self) -> None:
        preds = self.model.predict_match("test-match-id-jkl")
        for p in preds:
            assert isinstance(p["factors"], list)
            assert len(p["factors"]) > 0

    def test_expected_goals_positive(self) -> None:
        xg = self.model.compute_expected_goals("test-match-id-mno")
        assert xg["home"] > 0
        assert xg["away"] > 0


# ── Value formula ─────────────────────────────────────────────────────────────

class TestValueFormulas:
    def test_edge_calculation(self) -> None:
        model_prob = 0.55
        decimal_odds = 2.10
        implied_prob = 1 / decimal_odds
        edge = model_prob - implied_prob
        assert abs(edge - (0.55 - 1 / 2.10)) < 1e-9

    def test_expected_value_positive_when_edge_positive(self) -> None:
        model_prob = 0.60
        decimal_odds = 2.00
        ev = model_prob * (decimal_odds - 1) - (1 - model_prob)
        assert ev > 0

    def test_expected_value_negative_when_no_edge(self) -> None:
        model_prob = 0.45
        decimal_odds = 2.00  # implied = 0.50, edge = -0.05
        ev = model_prob * (decimal_odds - 1) - (1 - model_prob)
        assert ev < 0

    def test_accumulator_probability(self) -> None:
        probs = [0.6, 0.55, 0.7]
        combined = 1.0
        for p in probs:
            combined *= p
        assert abs(combined - 0.6 * 0.55 * 0.7) < 1e-9

    def test_value_flag_threshold(self) -> None:
        """Value flag appears when edge >= 0.03 and confidence is medium or high."""
        def has_value(model_prob: float, decimal_odds: float, confidence: str) -> bool:
            implied = 1 / decimal_odds
            edge = model_prob - implied
            return edge >= 0.03 and confidence in ("medium", "high")

        assert has_value(0.55, 2.20, "medium") is True
        assert has_value(0.50, 2.20, "medium") is False  # edge < 0.03
        assert has_value(0.55, 2.20, "low") is False  # low confidence


# ── NBA model ─────────────────────────────────────────────────────────────────

class TestNBAModel:
    def setup_method(self) -> None:
        self.model = NBAModel()

    def test_win_probabilities_sum_to_one(self) -> None:
        result = self.model.predict_match("nba-match-123")
        wp = result["win_probability"]
        assert abs(wp["home"] + wp["away"] - 1.0) < 1e-4

    def test_win_probabilities_in_range(self) -> None:
        result = self.model.predict_match("nba-match-456")
        wp = result["win_probability"]
        assert 0.0 <= wp["home"] <= 1.0
        assert 0.0 <= wp["away"] <= 1.0

    def test_player_props_structure(self) -> None:
        result = self.model.predict_player_props("player-123", "match-456")
        assert "points" in result
        assert "rebounds" in result
        assert "assists" in result
        assert "projection" in result["points"]
        assert "lines" in result["points"]

    def test_player_props_over_prob_in_range(self) -> None:
        result = self.model.predict_player_props("player-789", "match-012")
        for line_data in result["points"]["lines"]:
            assert 0.0 <= line_data["over"] <= 1.0