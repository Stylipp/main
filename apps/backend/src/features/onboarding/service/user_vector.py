"""Pure functions for computing user style vectors and price profiles.

Implements the Modified Rocchio algorithm for combining photo embeddings with
calibration swipe signals into a single user style vector, and IQR-based
price profiling from liked items.

Key formulas:
    User vector = 0.3 * avg(photo_embeddings)
                + 1.0 * avg(liked_embeddings)
                - 0.25 * avg(disliked_embeddings)
    (L2-normalized for cosine similarity search)

    NOTE: gamma=0.25 deviates from PROJECT.md's 0.7 per research recommendation
    (04-RESEARCH.md). The 0.7 weight is too aggressive for sparse calibration
    data (only ~5-6 dislikes). Standard Rocchio range is 0.15-0.25.
"""

from __future__ import annotations

import numpy as np

# Modified Rocchio weights
_ALPHA = 0.3  # Photo embedding weight (anchor signal)
_BETA = 1.0  # Liked embedding weight (positive signal)
_GAMMA = 0.25  # Disliked embedding weight (negative signal)


def compute_user_vector(
    photo_embeddings: list[list[float]],
    liked_embeddings: list[list[float]],
    disliked_embeddings: list[list[float]],
) -> list[float]:
    """Compute a user style vector using Modified Rocchio.

    Formula: alpha * avg(photos) + beta * avg(liked) - gamma * avg(disliked)
    Result is L2-normalized for cosine similarity search in Qdrant.

    Args:
        photo_embeddings: 1-2 photo embedding vectors (768-dim each).
        liked_embeddings: Embedding vectors of liked calibration products.
        disliked_embeddings: Embedding vectors of disliked calibration products.

    Returns:
        768-dimensional L2-normalized user style vector as list[float].

    Raises:
        ValueError: If photo_embeddings or liked_embeddings are empty.
    """
    if not photo_embeddings:
        raise ValueError("At least one photo embedding is required")
    if not liked_embeddings:
        raise ValueError("At least one liked embedding is required")

    # Compute component averages
    photo_avg = np.mean(np.array(photo_embeddings, dtype=np.float64), axis=0)
    liked_avg = np.mean(np.array(liked_embeddings, dtype=np.float64), axis=0)

    # Start with photo and liked components
    user_vector = _ALPHA * photo_avg + _BETA * liked_avg

    # Subtract disliked component if present
    if disliked_embeddings:
        disliked_avg = np.mean(np.array(disliked_embeddings, dtype=np.float64), axis=0)
        user_vector -= _GAMMA * disliked_avg

    # L2-normalize for cosine similarity
    norm = np.linalg.norm(user_vector)
    if norm > 0:
        user_vector = user_vector / norm

    return user_vector.tolist()


def initialize_price_profile(liked_prices: list[float]) -> dict:
    """Compute an IQR-based price profile from liked item prices.

    Uses only liked items (not disliked) because users may dislike an item
    for style reasons unrelated to price.

    If fewer than 3 prices are available, returns wide defaults using the
    median (if available) or a fallback of 50, with range 0.3x-3.0x.

    Args:
        liked_prices: Prices of liked calibration products.

    Returns:
        Dict with keys: price_min, price_max, price_median, price_std.
    """
    if not liked_prices:
        return {
            "price_min": 15.0,
            "price_max": 150.0,
            "price_median": 50.0,
            "price_std": 0.0,
        }

    prices = np.array(liked_prices, dtype=np.float64)

    if len(prices) < 3:
        median = float(np.median(prices))
        return {
            "price_min": round(median * 0.3, 2),
            "price_max": round(median * 3.0, 2),
            "price_median": round(median, 2),
            "price_std": round(float(np.std(prices)), 2),
        }

    # Full IQR-based computation
    median = float(np.median(prices))
    q1 = float(np.percentile(prices, 25))
    q3 = float(np.percentile(prices, 75))
    iqr = q3 - q1
    std = float(np.std(prices))

    price_min = max(0.0, q1 - 1.5 * iqr)
    price_max = q3 + 1.5 * iqr

    return {
        "price_min": round(price_min, 2),
        "price_max": round(price_max, 2),
        "price_median": round(median, 2),
        "price_std": round(std, 2),
    }
