from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import numpy as np
import pytest

from src.features.feedback.service import (
    profile_update_service as profile_update_module,
)
from src.features.feedback.service.profile_update_service import (
    PendingInteraction,
    ProfileUpdateService,
)


def make_service() -> ProfileUpdateService:
    return ProfileUpdateService(
        settings=SimpleNamespace(
            qdrant_collection="products",
            user_profiles_collection="user_profiles",
            profile_update_lr_new=0.15,
            profile_update_lr_mid=0.08,
            profile_update_lr_mature=0.03,
            profile_update_lr_mid_confidence=0.3,
            profile_update_lr_mature_confidence=0.7,
            profile_update_dislike_gamma=0.05,
            profile_update_max_delta=0.15,
            profile_update_price_alpha=0.1,
            profile_update_save_price_alpha=0.15,
            profile_update_dislike_burst_count=10,
            profile_update_dislike_burst_gamma_scale=0.5,
        )
    )


def test_get_learning_rate_uses_confidence_bands() -> None:
    service = make_service()

    assert service._get_learning_rate(0.1) == pytest.approx(0.15)
    assert service._get_learning_rate(0.5) == pytest.approx(0.08)
    assert service._get_learning_rate(0.8) == pytest.approx(0.03)


def test_apply_positive_signal_moves_vector_toward_product() -> None:
    service = make_service()
    user_vector = np.array([1.0, 0.0], dtype=np.float64)
    product_vector = np.array([0.0, 1.0], dtype=np.float64)

    updated = service._apply_interaction_update(
        user_vector=user_vector,
        product_vector=product_vector,
        action="like",
        profile_confidence=0.1,
        burst_active=False,
    )

    assert updated[1] > 0.0
    assert updated[0] < 1.0
    assert np.linalg.norm(updated) == pytest.approx(1.0, abs=1e-6)


def test_apply_dislike_signal_moves_vector_away_from_product() -> None:
    service = make_service()
    user_vector = np.array([1.0, 0.0], dtype=np.float64)
    product_vector = np.array([0.8, 0.6], dtype=np.float64)

    before = 1.0 - service._cosine_distance(user_vector, product_vector)
    updated = service._apply_interaction_update(
        user_vector=user_vector,
        product_vector=product_vector,
        action="dislike",
        profile_confidence=0.1,
        burst_active=False,
    )
    after = 1.0 - service._cosine_distance(updated, product_vector)

    assert after < before


def test_update_price_profile_uses_stronger_alpha_for_save() -> None:
    service = make_service()
    current_profile = {
        "price_min": 15.0,
        "price_max": 150.0,
        "price_median": 50.0,
        "price_std": 10.0,
    }

    liked = service._update_price_profile(
        current_profile=current_profile,
        price=100.0,
        action="like",
    )
    saved = service._update_price_profile(
        current_profile=current_profile,
        price=100.0,
        action="save",
    )

    assert liked["price_median"] == pytest.approx(55.0, abs=0.01)
    assert saved["price_median"] == pytest.approx(57.5, abs=0.01)
    assert saved["price_median"] > liked["price_median"]


@pytest.mark.asyncio
async def test_process_pending_updates_skips_when_user_vector_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = make_service()
    user_id = uuid4()
    user = SimpleNamespace(
        id=user_id,
        profile_version=1,
        interaction_count=20,
        profile_confidence=0.4,
        profile_source="onboarding",
        price_profile={},
        last_profile_update_at=None,
    )

    class FakeSessionContext:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def fake_load_user(session, requested_user_id):
        assert requested_user_id == user_id
        return user

    async def fake_pending(session, loaded_user):
        assert loaded_user is user
        return [
            PendingInteraction(
                product_id="product-1",
                action="like",
                price=89.0,
                created_at=datetime.now(timezone.utc),
            )
        ]

    async def fake_profile_point(qdrant, requested_user_id):
        assert requested_user_id == user_id
        return None, {}

    async def fake_qdrant():
        return SimpleNamespace()

    monkeypatch.setattr(
        profile_update_module,
        "_get_session_factory",
        lambda: lambda: FakeSessionContext(),
    )
    monkeypatch.setattr(profile_update_module, "_get_qdrant", fake_qdrant)
    monkeypatch.setattr(service, "_load_user", fake_load_user)
    monkeypatch.setattr(service, "_load_pending_interactions", fake_pending)
    monkeypatch.setattr(service, "_load_user_profile_point", fake_profile_point)

    processed = await service.process_pending_updates(user_id)

    assert processed == 0


@pytest.mark.asyncio
async def test_process_pending_updates_applies_batch_and_persists_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = make_service()
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    user = SimpleNamespace(
        id=user_id,
        profile_version=2,
        interaction_count=25,
        profile_confidence=0.45,
        profile_source="onboarding",
        price_profile={
            "price_min": 15.0,
            "price_max": 150.0,
            "price_median": 50.0,
            "price_std": 10.0,
        },
        last_profile_update_at=now - timedelta(minutes=5),
    )
    interactions = [
        PendingInteraction(
            product_id="product-1",
            action="like",
            price=80.0,
            created_at=now - timedelta(minutes=2),
        ),
        PendingInteraction(
            product_id="product-2",
            action="save",
            price=120.0,
            created_at=now - timedelta(minutes=1),
        ),
    ]
    persisted: dict[str, object] = {}
    qdrant_calls: list[dict] = []

    class FakeSessionContext:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeQdrant:
        async def upsert(self, **kwargs):
            qdrant_calls.append(kwargs)

    async def fake_qdrant():
        return FakeQdrant()

    async def fake_load_user(session, requested_user_id):
        assert requested_user_id == user_id
        return user

    async def fake_pending(session, loaded_user):
        assert loaded_user is user
        return interactions

    async def fake_profile_point(qdrant, requested_user_id):
        assert requested_user_id == user_id
        return [1.0, 0.0], {"photo_count": 2}

    async def fake_recent_dislike_burst(session, requested_user_id):
        assert requested_user_id == user_id
        return False

    async def fake_product_vectors(qdrant, product_ids):
        assert product_ids == ["product-1", "product-2"]
        return {
            "product-1": [0.8, 0.2],
            "product-2": [0.2, 0.8],
        }

    async def fake_commit(
        *,
        session,
        user,
        next_price_profile,
        next_profile_version,
        next_profile_confidence,
        next_profile_source,
        last_processed_at,
    ):
        persisted.update(
            {
                "price_profile": next_price_profile,
                "version": next_profile_version,
                "confidence": next_profile_confidence,
                "source": next_profile_source,
                "last_processed_at": last_processed_at,
            }
        )
        return True

    monkeypatch.setattr(
        profile_update_module,
        "_get_session_factory",
        lambda: lambda: FakeSessionContext(),
    )
    monkeypatch.setattr(profile_update_module, "_get_qdrant", fake_qdrant)
    monkeypatch.setattr(service, "_load_user", fake_load_user)
    monkeypatch.setattr(service, "_load_pending_interactions", fake_pending)
    monkeypatch.setattr(service, "_load_user_profile_point", fake_profile_point)
    monkeypatch.setattr(service, "_has_recent_dislike_burst", fake_recent_dislike_burst)
    monkeypatch.setattr(service, "_load_product_vectors", fake_product_vectors)
    monkeypatch.setattr(service, "_commit_user_profile_update", fake_commit)

    processed = await service.process_pending_updates(user_id)

    assert processed == 2
    assert persisted["version"] == 3
    assert persisted["source"] == "learning"
    assert persisted["last_processed_at"] == interactions[-1].created_at
    assert persisted["price_profile"]["price_median"] > 50.0
    assert len(qdrant_calls) == 1


@pytest.mark.asyncio
async def test_process_pending_updates_discards_stale_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = make_service()
    user_id = uuid4()
    user = SimpleNamespace(
        id=user_id,
        profile_version=4,
        interaction_count=60,
        profile_confidence=0.75,
        profile_source="learning",
        price_profile={},
        last_profile_update_at=None,
    )

    class FakeSessionContext:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeQdrant:
        async def upsert(self, **kwargs):
            return None

    async def fake_qdrant():
        return FakeQdrant()

    async def fake_load_user(session, requested_user_id):
        return user

    async def fake_pending(session, loaded_user):
        return [
            PendingInteraction(
                product_id="product-1",
                action="like",
                price=50.0,
                created_at=datetime.now(timezone.utc),
            )
        ]

    async def fake_profile_point(qdrant, requested_user_id):
        return [1.0, 0.0], {}

    async def fake_recent_dislike_burst(session, requested_user_id):
        return False

    async def fake_product_vectors(qdrant, product_ids):
        return {"product-1": [0.0, 1.0]}

    async def fake_commit(**kwargs):
        return False

    monkeypatch.setattr(
        profile_update_module,
        "_get_session_factory",
        lambda: lambda: FakeSessionContext(),
    )
    monkeypatch.setattr(profile_update_module, "_get_qdrant", fake_qdrant)
    monkeypatch.setattr(service, "_load_user", fake_load_user)
    monkeypatch.setattr(service, "_load_pending_interactions", fake_pending)
    monkeypatch.setattr(service, "_load_user_profile_point", fake_profile_point)
    monkeypatch.setattr(service, "_has_recent_dislike_burst", fake_recent_dislike_burst)
    monkeypatch.setattr(service, "_load_product_vectors", fake_product_vectors)
    monkeypatch.setattr(service, "_commit_user_profile_update", fake_commit)

    processed = await service.process_pending_updates(user_id)

    assert processed == 0
