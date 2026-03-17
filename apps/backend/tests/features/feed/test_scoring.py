from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.features.feed.utils.scoring import (
    compute_freshness_score,
    compute_price_affinity,
    normalize_scores,
)
from src.features.feed.service.ranking_service import (
    RankedCandidate,
    rank_candidates,
)


# ---------------------------------------------------------------------------
# compute_freshness_score
# ---------------------------------------------------------------------------


class TestComputeFreshnessScore:
    def test_just_created_returns_approximately_one(self) -> None:
        now = datetime.now(timezone.utc)
        score = compute_freshness_score(now)
        assert score == pytest.approx(1.0, abs=0.01)

    def test_14_days_ago_returns_approximately_half(self) -> None:
        created = datetime.now(timezone.utc) - timedelta(days=14)
        score = compute_freshness_score(created)
        assert score == pytest.approx(0.5, abs=0.01)

    def test_28_days_ago_returns_approximately_quarter(self) -> None:
        created = datetime.now(timezone.utc) - timedelta(days=28)
        score = compute_freshness_score(created)
        assert score == pytest.approx(0.25, abs=0.01)

    def test_same_instant_returns_one(self) -> None:
        created = datetime.now(timezone.utc)
        score = compute_freshness_score(created)
        assert score == pytest.approx(1.0, abs=0.001)

    def test_future_date_returns_one(self) -> None:
        future = datetime.now(timezone.utc) + timedelta(days=7)
        score = compute_freshness_score(future)
        assert score == pytest.approx(1.0, abs=0.001)

    def test_very_old_item_approaches_zero(self) -> None:
        old = datetime.now(timezone.utc) - timedelta(days=365)
        score = compute_freshness_score(old)
        assert 0.0 <= score < 0.01

    def test_score_is_monotonically_decreasing(self) -> None:
        now = datetime.now(timezone.utc)
        scores = [
            compute_freshness_score(now - timedelta(days=d))
            for d in [0, 7, 14, 21, 28]
        ]
        for i in range(len(scores) - 1):
            assert scores[i] > scores[i + 1]

    def test_return_type_is_float(self) -> None:
        score = compute_freshness_score(datetime.now(timezone.utc))
        assert isinstance(score, float)


# ---------------------------------------------------------------------------
# compute_price_affinity
# ---------------------------------------------------------------------------


class TestComputePriceAffinity:
    def test_price_at_median_returns_approximately_one(self) -> None:
        score = compute_price_affinity(50.0, 50.0, 15.0)
        assert score == pytest.approx(1.0, abs=0.01)

    def test_price_double_median_less_than_one(self) -> None:
        score = compute_price_affinity(100.0, 50.0, 15.0)
        assert 0.0 < score < 1.0

    def test_price_half_median_less_than_one(self) -> None:
        score = compute_price_affinity(25.0, 50.0, 15.0)
        assert 0.0 < score < 1.0

    def test_symmetric_in_log_space(self) -> None:
        score_double = compute_price_affinity(100.0, 50.0, 15.0)
        score_half = compute_price_affinity(25.0, 50.0, 15.0)
        assert score_double == pytest.approx(score_half, abs=0.01)

    def test_price_zero_returns_neutral(self) -> None:
        score = compute_price_affinity(0.0, 50.0, 15.0)
        assert score == 0.5

    def test_price_negative_returns_neutral(self) -> None:
        score = compute_price_affinity(-10.0, 50.0, 15.0)
        assert score == 0.5

    def test_median_zero_returns_neutral(self) -> None:
        score = compute_price_affinity(50.0, 0.0, 15.0)
        assert score == 0.5

    def test_median_negative_returns_neutral(self) -> None:
        score = compute_price_affinity(50.0, -10.0, 15.0)
        assert score == 0.5

    def test_small_std_uses_minimum_sigma(self) -> None:
        # sigma = max(price_std, price_median * 0.3)
        # With tiny std, sigma should be price_median * 0.3 = 15.0
        score = compute_price_affinity(50.0, 50.0, 0.01)
        assert score == pytest.approx(1.0, abs=0.01)

    def test_return_type_is_float(self) -> None:
        score = compute_price_affinity(50.0, 50.0, 15.0)
        assert isinstance(score, float)

    def test_score_always_between_zero_and_one(self) -> None:
        test_cases = [
            (1.0, 100.0, 10.0),
            (1000.0, 50.0, 5.0),
            (50.0, 50.0, 50.0),
            (0.01, 100.0, 30.0),
        ]
        for price, median, std in test_cases:
            score = compute_price_affinity(price, median, std)
            assert 0.0 <= score <= 1.0, f"Failed for ({price}, {median}, {std})"


# ---------------------------------------------------------------------------
# normalize_scores
# ---------------------------------------------------------------------------


class TestNormalizeScores:
    def test_basic_normalization(self) -> None:
        result = normalize_scores([0.2, 0.5, 0.8])
        assert result == pytest.approx([0.0, 0.5, 1.0], abs=0.001)

    def test_uniform_scores_return_all_half(self) -> None:
        result = normalize_scores([0.5, 0.5, 0.5])
        assert result == [0.5, 0.5, 0.5]

    def test_empty_list_returns_empty(self) -> None:
        result = normalize_scores([])
        assert result == []

    def test_single_element_returns_half(self) -> None:
        result = normalize_scores([0.7])
        assert result == [0.5]

    def test_two_elements(self) -> None:
        result = normalize_scores([0.3, 0.9])
        assert result == pytest.approx([0.0, 1.0], abs=0.001)

    def test_already_normalized(self) -> None:
        result = normalize_scores([0.0, 0.5, 1.0])
        assert result == pytest.approx([0.0, 0.5, 1.0], abs=0.001)

    def test_negative_values(self) -> None:
        result = normalize_scores([-1.0, 0.0, 1.0])
        assert result == pytest.approx([0.0, 0.5, 1.0], abs=0.001)

    def test_return_type_is_list_of_floats(self) -> None:
        result = normalize_scores([0.2, 0.8])
        assert isinstance(result, list)
        assert all(isinstance(v, float) for v in result)

    def test_near_uniform_scores_return_all_half(self) -> None:
        result = normalize_scores([0.5, 0.5 + 1e-12, 0.5 - 1e-12])
        assert result == [0.5, 0.5, 0.5]


# ---------------------------------------------------------------------------
# RankedCandidate dataclass
# ---------------------------------------------------------------------------


class TestRankedCandidate:
    def test_fields_present(self) -> None:
        rc = RankedCandidate(
            product_id="p1",
            score=0.9,
            cosine_score=0.8,
            cluster_prior_score=0.7,
            price_score=0.6,
            freshness_score=0.5,
        )
        assert rc.product_id == "p1"
        assert rc.score == 0.9
        assert rc.cosine_score == 0.8
        assert rc.cluster_prior_score == 0.7
        assert rc.price_score == 0.6
        assert rc.freshness_score == 0.5


# ---------------------------------------------------------------------------
# rank_candidates
# ---------------------------------------------------------------------------


def _make_candidate(
    product_id: str,
    cosine_score: float,
    price: float,
    created_at: str,
    cluster_id: int,
) -> SimpleNamespace:
    """Mimics a Qdrant ScoredPoint with payload."""
    return SimpleNamespace(
        score=cosine_score,
        payload={
            "product_id": product_id,
            "price": price,
            "created_at": created_at,
            "cluster_id": cluster_id,
        },
    )


class TestRankCandidates:
    def test_empty_candidates_returns_empty(self) -> None:
        result = rank_candidates(
            candidates=[],
            user_price_profile={"median": 50.0, "std": 15.0},
            cluster_priors={},
        )
        assert result == []

    def test_single_candidate(self) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        candidates = [_make_candidate("p1", 0.9, 50.0, now_iso, 1)]
        result = rank_candidates(
            candidates=candidates,
            user_price_profile={"median": 50.0, "std": 15.0},
            cluster_priors={1: 0.8},
        )
        assert len(result) == 1
        assert result[0].product_id == "p1"
        assert isinstance(result[0], RankedCandidate)
        assert isinstance(result[0].score, float)

    def test_three_candidates_correct_ordering(self) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        old_iso = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

        candidates = [
            # High cosine, fresh, good price, strong cluster
            _make_candidate("best", 0.95, 50.0, now_iso, 1),
            # Medium cosine, old, bad price, weak cluster
            _make_candidate("worst", 0.3, 200.0, old_iso, 3),
            # Medium cosine, fresh, good price, medium cluster
            _make_candidate("mid", 0.7, 55.0, now_iso, 2),
        ]

        result = rank_candidates(
            candidates=candidates,
            user_price_profile={"median": 50.0, "std": 15.0},
            cluster_priors={1: 0.9, 2: 0.5, 3: 0.1},
        )

        assert len(result) == 3
        assert result[0].product_id == "best"
        assert result[-1].product_id == "worst"
        # Scores should be descending
        assert result[0].score >= result[1].score >= result[2].score

    def test_returns_ranked_candidate_instances(self) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        candidates = [_make_candidate("p1", 0.9, 50.0, now_iso, 1)]
        result = rank_candidates(
            candidates=candidates,
            user_price_profile={"median": 50.0, "std": 15.0},
            cluster_priors={1: 0.8},
        )
        assert all(isinstance(rc, RankedCandidate) for rc in result)

    def test_all_same_scores_no_crash(self) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        candidates = [
            _make_candidate("p1", 0.5, 50.0, now_iso, 1),
            _make_candidate("p2", 0.5, 50.0, now_iso, 1),
            _make_candidate("p3", 0.5, 50.0, now_iso, 1),
        ]
        result = rank_candidates(
            candidates=candidates,
            user_price_profile={"median": 50.0, "std": 15.0},
            cluster_priors={1: 0.5},
        )
        assert len(result) == 3

    def test_missing_cluster_prior_defaults_to_zero(self) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        candidates = [_make_candidate("p1", 0.9, 50.0, now_iso, 99)]
        result = rank_candidates(
            candidates=candidates,
            user_price_profile={"median": 50.0, "std": 15.0},
            cluster_priors={1: 0.8},  # cluster 99 not present
        )
        assert len(result) == 1
        assert isinstance(result[0].score, float)

    def test_score_weights_sum_to_one(self) -> None:
        # Verify the weights used internally sum to 1.0
        # We test this indirectly: a candidate with all factors at maximum
        # should have a score close to 1.0 after normalization of a single item
        now_iso = datetime.now(timezone.utc).isoformat()
        candidates = [_make_candidate("p1", 0.99, 50.0, now_iso, 1)]
        result = rank_candidates(
            candidates=candidates,
            user_price_profile={"median": 50.0, "std": 15.0},
            cluster_priors={1: 0.99},
        )
        # Single candidate: all normalized factors become 0.5
        # Final score = 0.65*0.5 + 0.15*0.5 + 0.10*0.5 + 0.10*0.5 = 0.5
        assert result[0].score == pytest.approx(0.5, abs=0.01)

    def test_component_scores_populated(self) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        candidates = [
            _make_candidate("p1", 0.9, 50.0, now_iso, 1),
            _make_candidate("p2", 0.5, 100.0, now_iso, 2),
        ]
        result = rank_candidates(
            candidates=candidates,
            user_price_profile={"median": 50.0, "std": 15.0},
            cluster_priors={1: 0.8, 2: 0.3},
        )
        for rc in result:
            assert rc.cosine_score is not None
            assert rc.cluster_prior_score is not None
            assert rc.price_score is not None
            assert rc.freshness_score is not None
