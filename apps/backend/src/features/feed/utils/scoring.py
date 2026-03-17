"""Pure scoring utility functions for the feed ranking pipeline.

All functions are side-effect-free and depend only on stdlib (math, datetime).
"""

import math
from datetime import datetime, timezone

FRESHNESS_LAMBDA = math.log(2) / 14  # 14-day half-life


def compute_freshness_score(created_at: datetime) -> float:
    """Exponential decay freshness score with a 14-day half-life.

    Returns ~1.0 for items created now, ~0.5 at 14 days, ~0.25 at 28 days.
    Future dates are clamped to 1.0.
    """
    now = datetime.now(timezone.utc)
    days_old = max((now - created_at).total_seconds() / 86400, 0)
    return math.exp(-FRESHNESS_LAMBDA * days_old)


def compute_price_affinity(
    product_price: float,
    price_median: float,
    price_std: float,
) -> float:
    """Log-normal Gaussian affinity between a product price and a user's price profile.

    Returns ~1.0 when product_price equals price_median.
    Returns 0.5 (neutral fallback) if either price or median is non-positive.
    """
    if product_price <= 0 or price_median <= 0:
        return 0.5

    log_price = math.log(product_price)
    log_median = math.log(price_median)
    sigma = max(price_std, price_median * 0.3)
    log_sigma = max(math.log(sigma), 0.1)

    exponent = -((log_price - log_median) ** 2) / (2 * log_sigma**2)
    return math.exp(exponent)


def normalize_scores(scores: list[float]) -> list[float]:
    """Min-max normalization to [0, 1].

    Uniform scores map to 0.5. Empty input returns empty. Single element returns [0.5].
    """
    if not scores:
        return []

    minimum = min(scores)
    maximum = max(scores)
    spread = maximum - minimum

    if spread < 1e-8:
        return [0.5] * len(scores)

    return [(score - minimum) / spread for score in scores]
