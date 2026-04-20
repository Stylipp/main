"""Asynchronous user profile updates driven by recorded feedback.

This service batches any interactions recorded since the user's last successful
profile update and applies them to the user's vector in Qdrant. The write path
is intentionally decoupled from the swipe request via FastAPI BackgroundTasks.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

import numpy as np
from qdrant_client.models import PointStruct
from sqlalchemy import select, update

from src.core.config import Settings, get_settings
from src.core.profile_state import compute_profile_confidence
from src.models.product import Product
from src.models.user import User
from src.models.user_interaction import UserInteraction

logger = logging.getLogger(__name__)

_POSITIVE_SIGNAL_WEIGHTS = {
    "like": 1.0,
    "save": 1.5,
}
_NEGATIVE_SIGNAL_WEIGHTS = {
    "dislike": -1.0,
}
_USER_PROFILE_LOCKS: dict[str, asyncio.Lock] = {}


@dataclass
class PendingInteraction:
    product_id: str
    action: str
    price: float
    created_at: datetime


def _get_session_factory():
    from src.core.database import SessionLocal

    return SessionLocal


async def _get_qdrant():
    from src.core.qdrant import get_qdrant_client

    return await get_qdrant_client()


class ProfileUpdateService:
    """Apply pending feedback interactions to a user's learned profile."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def process_pending_updates(self, user_id: UUID) -> int:
        """Process all interactions recorded since the last successful update.

        Returns the number of interactions consumed by this update pass.
        """
        lock = _USER_PROFILE_LOCKS.setdefault(str(user_id), asyncio.Lock())
        async with lock:
            return await self._process_pending_updates_locked(user_id)

    async def _process_pending_updates_locked(self, user_id: UUID) -> int:
        session_factory = _get_session_factory()
        async with session_factory() as session:
            user = await self._load_user(session, user_id)
            if user is None:
                logger.warning("Skipping profile update for missing user=%s", user_id)
                return 0

            pending_interactions = await self._load_pending_interactions(session, user)
            if not pending_interactions:
                return 0

            qdrant = await _get_qdrant()
            current_vector, payload = await self._load_user_profile_point(
                qdrant, user_id
            )
            if current_vector is None:
                logger.info(
                    "Skipping profile update for user=%s: no user vector exists yet",
                    user_id,
                )
                return 0

            burst_active = await self._has_recent_dislike_burst(session, user_id)
            product_vectors = await self._load_product_vectors(
                qdrant,
                [interaction.product_id for interaction in pending_interactions],
            )

            new_vector = np.array(current_vector, dtype=np.float64)
            new_price_profile = dict(user.price_profile or {})
            applied_count = 0

            for interaction in pending_interactions:
                product_vector = product_vectors.get(interaction.product_id)
                if product_vector is None:
                    logger.warning(
                        "Skipping profile update interaction for missing product vector user=%s product=%s",
                        user_id,
                        interaction.product_id,
                    )
                    continue

                new_vector = self._apply_interaction_update(
                    user_vector=new_vector,
                    product_vector=np.array(product_vector, dtype=np.float64),
                    action=interaction.action,
                    profile_confidence=user.profile_confidence,
                    burst_active=burst_active,
                )
                new_price_profile = self._update_price_profile(
                    current_profile=new_price_profile,
                    price=interaction.price,
                    action=interaction.action,
                )
                applied_count += 1

            if applied_count == 0:
                return 0

            last_processed_at = pending_interactions[-1].created_at
            next_version = user.profile_version + 1
            next_confidence = compute_profile_confidence(user.interaction_count)
            next_source = self._resolve_profile_source(user.profile_source)
            next_payload = {
                **payload,
                "user_id": str(user_id),
                "profile_version": next_version,
                "profile_source": next_source,
                "interaction_count": user.interaction_count,
                "last_profile_update_at": last_processed_at.isoformat(),
            }

            await qdrant.upsert(
                collection_name=self._settings.user_profiles_collection,
                points=[
                    PointStruct(
                        id=str(user_id),
                        vector=new_vector.tolist(),
                        payload=next_payload,
                    )
                ],
            )

            updated = await self._commit_user_profile_update(
                session=session,
                user=user,
                next_price_profile=new_price_profile,
                next_profile_version=next_version,
                next_profile_confidence=next_confidence,
                next_profile_source=next_source,
                last_processed_at=last_processed_at,
            )
            if not updated:
                logger.info(
                    "Discarded stale profile update for user=%s expected_version=%d",
                    user_id,
                    user.profile_version,
                )
                return 0

            logger.info(
                "Processed %d profile interactions for user=%s -> version=%d",
                len(pending_interactions),
                user_id,
                next_version,
            )
            return len(pending_interactions)

    async def _load_user(self, session, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _load_pending_interactions(
        self,
        session,
        user: User,
    ) -> list[PendingInteraction]:
        stmt = (
            select(
                UserInteraction.action,
                UserInteraction.created_at,
                Product.id,
                Product.price,
            )
            .join(Product, Product.id == UserInteraction.product_id)
            .where(UserInteraction.user_id == user.id)
            .order_by(UserInteraction.created_at.asc(), UserInteraction.id.asc())
        )
        if user.last_profile_update_at is not None:
            stmt = stmt.where(UserInteraction.created_at > user.last_profile_update_at)

        result = await session.execute(stmt)
        return [
            PendingInteraction(
                product_id=str(row.id),
                action=row.action,
                price=float(row.price),
                created_at=self._coerce_timestamp(row.created_at),
            )
            for row in result.all()
        ]

    async def _load_user_profile_point(
        self,
        qdrant,
        user_id: UUID,
    ) -> tuple[list[float] | None, dict]:
        points = await qdrant.retrieve(
            collection_name=self._settings.user_profiles_collection,
            ids=[str(user_id)],
            with_vectors=True,
            with_payload=True,
        )
        if not points or points[0].vector is None:
            return None, {}
        return points[0].vector, dict(points[0].payload or {})

    async def _load_product_vectors(
        self,
        qdrant,
        product_ids: list[str],
    ) -> dict[str, list[float]]:
        unique_ids = list(dict.fromkeys(product_ids))
        if not unique_ids:
            return {}

        points = await qdrant.retrieve(
            collection_name=self._settings.qdrant_collection,
            ids=unique_ids,
            with_vectors=True,
            with_payload=False,
        )
        vectors: dict[str, list[float]] = {}
        for point in points:
            if point.vector is None:
                continue
            vectors[str(point.id)] = point.vector
        return vectors

    async def _has_recent_dislike_burst(self, session, user_id: UUID) -> bool:
        limit = self._settings.profile_update_dislike_burst_count
        stmt = (
            select(UserInteraction.action)
            .where(UserInteraction.user_id == user_id)
            .order_by(UserInteraction.created_at.desc(), UserInteraction.id.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        recent_actions = [row.action for row in result.all()]
        if len(recent_actions) < limit:
            return False
        return all(action == "dislike" for action in recent_actions)

    async def _commit_user_profile_update(
        self,
        *,
        session,
        user: User,
        next_price_profile: dict,
        next_profile_version: int,
        next_profile_confidence: float,
        next_profile_source: str | None,
        last_processed_at: datetime,
    ) -> bool:
        stmt = (
            update(User)
            .where(User.id == user.id, User.profile_version == user.profile_version)
            .values(
                profile_version=next_profile_version,
                last_profile_update_at=last_processed_at,
                price_profile=next_price_profile,
                profile_confidence=next_profile_confidence,
                profile_source=next_profile_source,
            )
        )
        result = await session.execute(stmt)
        if result.rowcount != 1:
            await session.rollback()
            return False

        await session.commit()
        return True

    def _apply_interaction_update(
        self,
        *,
        user_vector: np.ndarray,
        product_vector: np.ndarray,
        action: str,
        profile_confidence: float,
        burst_active: bool,
    ) -> np.ndarray:
        """Apply a single interaction to the user vector with guardrails."""
        learning_rate = self._get_learning_rate(profile_confidence)
        product_vector = self._normalize_vector(product_vector)
        signal_weight = self._get_signal_weight(action)
        if signal_weight == 0.0:
            return user_vector

        if signal_weight > 0:
            effective_lr = min(learning_rate * signal_weight, 0.35)
            candidate = self._normalize_vector(
                (1.0 - effective_lr) * user_vector + effective_lr * product_vector
            )
        else:
            gamma = self._settings.profile_update_dislike_gamma
            if burst_active:
                gamma *= self._settings.profile_update_dislike_burst_gamma_scale
            candidate = self._normalize_vector(
                (1.0 - learning_rate) * user_vector
                - abs(signal_weight) * gamma * product_vector
            )

        return self._limit_delta(user_vector, candidate)

    def _get_learning_rate(self, profile_confidence: float) -> float:
        if profile_confidence < self._settings.profile_update_lr_mid_confidence:
            return self._settings.profile_update_lr_new
        if profile_confidence < self._settings.profile_update_lr_mature_confidence:
            return self._settings.profile_update_lr_mid
        return self._settings.profile_update_lr_mature

    def _get_signal_weight(self, action: str) -> float:
        if action in _POSITIVE_SIGNAL_WEIGHTS:
            return _POSITIVE_SIGNAL_WEIGHTS[action]
        return _NEGATIVE_SIGNAL_WEIGHTS.get(action, 0.0)

    def _update_price_profile(
        self,
        *,
        current_profile: dict,
        price: float,
        action: str,
    ) -> dict:
        """Update the stored price profile using an EMA on positive signals."""
        if action not in _POSITIVE_SIGNAL_WEIGHTS:
            return current_profile

        if not current_profile:
            return {
                "price_min": round(price * 0.3, 2),
                "price_max": round(price * 3.0, 2),
                "price_median": round(price, 2),
                "price_std": 0.0,
            }

        median = float(current_profile.get("price_median", price))
        std = float(current_profile.get("price_std", 0.0))
        price_min = float(current_profile.get("price_min", median * 0.3))
        price_max = float(current_profile.get("price_max", median * 3.0))

        alpha = self._settings.profile_update_price_alpha
        if action == "save":
            alpha = self._settings.profile_update_save_price_alpha

        lower_ratio = price_min / median if median > 0 else 0.3
        upper_ratio = price_max / median if median > 0 else 3.0
        next_median = alpha * price + (1.0 - alpha) * median
        next_std = alpha * abs(price - next_median) + (1.0 - alpha) * std

        return {
            "price_min": round(max(0.0, next_median * lower_ratio), 2),
            "price_max": round(max(next_median, next_median * upper_ratio), 2),
            "price_median": round(next_median, 2),
            "price_std": round(next_std, 2),
        }

    def _limit_delta(
        self, old_vector: np.ndarray, new_vector: np.ndarray
    ) -> np.ndarray:
        actual_delta = self._cosine_distance(old_vector, new_vector)
        max_delta = self._settings.profile_update_max_delta
        if actual_delta <= max_delta:
            return new_vector

        ratio = max_delta / actual_delta
        return self._normalize_vector((1.0 - ratio) * old_vector + ratio * new_vector)

    @staticmethod
    def _normalize_vector(vector: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm

    @staticmethod
    def _cosine_distance(left: np.ndarray, right: np.ndarray) -> float:
        left_norm = np.linalg.norm(left)
        right_norm = np.linalg.norm(right)
        if left_norm == 0 or right_norm == 0:
            return 0.0
        similarity = float(np.dot(left, right) / (left_norm * right_norm))
        similarity = max(-1.0, min(1.0, similarity))
        return 1.0 - similarity

    @staticmethod
    def _resolve_profile_source(current_source: str | None) -> str | None:
        if current_source in {None, "onboarding", "learning"}:
            return "learning"
        return current_source

    @staticmethod
    def _coerce_timestamp(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
