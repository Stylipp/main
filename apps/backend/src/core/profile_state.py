"""Shared helpers for user profile maturity state.

These functions keep the "brain" metadata consistent across onboarding,
feedback ingestion, and future background profile updates.
"""

from __future__ import annotations

import math

_PROFILE_CONFIDENCE_TARGET = 200


def compute_profile_confidence(interaction_count: int) -> float:
    """Map total user interactions to a maturity score in ``[0.0, 1.0]``.

    The formula follows THE_BRAIN.md:

        confidence = min(1.0, log(1 + interaction_count) / log(1 + 200))

    Args:
        interaction_count: Total number of recorded interactions for the user.

    Returns:
        A bounded confidence score where 0.0 means brand new and 1.0 means
        mature enough for stable profile updates.
    """
    safe_count = max(interaction_count, 0)
    if safe_count == 0:
        return 0.0

    confidence = math.log1p(safe_count) / math.log1p(_PROFILE_CONFIDENCE_TARGET)
    return min(1.0, confidence)
