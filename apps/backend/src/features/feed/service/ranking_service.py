"""Multi-factor ranking service for the feed pipeline.

Combines cosine similarity, cluster prior, price affinity, and freshness
into a single weighted score for candidate ranking.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from src.features.feed.utils.scoring import (
    compute_freshness_score,
    compute_price_affinity,
    normalize_scores,
)

# Ranking weights (must sum to 1.0)
W_COSINE = 0.65
W_CLUSTER_PRIOR = 0.15
W_PRICE = 0.10
W_FRESHNESS = 0.10


@dataclass
class RankedCandidate:
    """A product candidate with its final weighted score and individual components."""

    product_id: str
    score: float
    cosine_score: float
    cluster_prior_score: float
    price_score: float
    freshness_score: float
    source: str = "personalized"


def rank_candidates(
    candidates: list,
    user_price_profile: dict,
    cluster_priors: dict,
) -> list[RankedCandidate]:
    """Rank candidates using multi-factor weighted scoring.

    Each factor is normalized across the candidate batch before weighting
    to prevent any single factor from dominating.

    Args:
        candidates: Qdrant ScoredPoint objects with payload containing
            product_id, price, created_at, cluster_id.
        user_price_profile: Dict with 'median' and 'std' keys.
        cluster_priors: Dict mapping cluster_id -> prior score (0-1).

    Returns:
        List of RankedCandidate sorted descending by final_score.
    """
    if not candidates:
        return []

    price_median = user_price_profile.get("median", 0.0)
    price_std = user_price_profile.get("std", 0.0)

    # Extract raw scores for each factor
    raw_cosine = []
    raw_cluster = []
    raw_price = []
    raw_freshness = []

    for candidate in candidates:
        payload = candidate.payload or {}

        raw_cosine.append(candidate.score)
        raw_cluster.append(cluster_priors.get(payload.get("cluster_id", 0), 0.0))
        raw_price.append(
            compute_price_affinity(
                float(payload.get("price", 0.0)), price_median, price_std
            )
        )

        created_at = payload.get("created_at", datetime.now(timezone.utc))
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        raw_freshness.append(compute_freshness_score(created_at))

    # Normalize each factor to [0, 1] within the batch
    norm_cosine = normalize_scores(raw_cosine)
    norm_cluster = normalize_scores(raw_cluster)
    norm_price = normalize_scores(raw_price)
    norm_freshness = normalize_scores(raw_freshness)

    # Compute weighted final scores and build result
    results = []
    for i, candidate in enumerate(candidates):
        payload = candidate.payload or {}
        final_score = (
            W_COSINE * norm_cosine[i]
            + W_CLUSTER_PRIOR * norm_cluster[i]
            + W_PRICE * norm_price[i]
            + W_FRESHNESS * norm_freshness[i]
        )

        results.append(
            RankedCandidate(
                product_id=str(payload.get("product_id", "")),
                score=final_score,
                cosine_score=norm_cosine[i],
                cluster_prior_score=norm_cluster[i],
                price_score=norm_price[i],
                freshness_score=norm_freshness[i],
            )
        )

    results.sort(key=lambda rc: rc.score, reverse=True)
    return results
