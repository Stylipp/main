from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from src.features.feed.schemas.schemas import FeedMode
from src.features.feed.service.feed_service import FeedService


def make_service() -> FeedService:
    return FeedService(
        qdrant_client=None,
        settings=SimpleNamespace(
            feed_hybrid_confidence_threshold=0.6,
            feed_hybrid_personalized_ratio=0.6,
            feed_personalized_discovery_count=2,
        ),
    )


def test_prepare_candidates_defaults_missing_cluster_id() -> None:
    candidates = [
        SimpleNamespace(
            score=0.91,
            payload={
                "product_id": "product-1",
                "price": 49.99,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )
    ]

    prepared = FeedService._prepare_candidates_for_ranking(
        candidates,
        source="test",
    )

    assert len(prepared) == 1
    assert prepared[0].payload["cluster_id"] == 0


def test_prepare_candidates_drops_missing_required_payload_fields() -> None:
    candidates = [
        SimpleNamespace(
            score=0.75,
            payload={
                "price": 49.99,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )
    ]

    prepared = FeedService._prepare_candidates_for_ranking(
        candidates,
        source="test",
    )

    assert prepared == []


def test_select_feed_mode_returns_trending_without_vector() -> None:
    service = make_service()

    feed_mode = service._select_feed_mode(user_vector=None, profile_confidence=0.9)

    assert feed_mode is FeedMode.TRENDING


def test_select_feed_mode_returns_hybrid_for_thin_profile() -> None:
    service = make_service()

    feed_mode = service._select_feed_mode(
        user_vector=[0.1, 0.2],
        profile_confidence=0.35,
    )

    assert feed_mode is FeedMode.HYBRID


def test_select_feed_mode_returns_personalized_for_mature_profile() -> None:
    service = make_service()

    feed_mode = service._select_feed_mode(
        user_vector=[0.1, 0.2],
        profile_confidence=0.8,
    )

    assert feed_mode is FeedMode.PERSONALIZED


def test_rank_trending_candidates_prefers_popularity_then_freshness() -> None:
    now = datetime.now(timezone.utc)
    candidates = [
        SimpleNamespace(
            product_id="popular",
            popularity=12.0,
            created_at=now,
        ),
        SimpleNamespace(
            product_id="fresh",
            popularity=4.0,
            created_at=now,
        ),
        SimpleNamespace(
            product_id="stale",
            popularity=1.0,
            created_at=now.replace(year=now.year - 1),
        ),
    ]

    ranked = FeedService._rank_trending_candidates(candidates)

    assert [candidate.product_id for candidate in ranked] == [
        "popular",
        "fresh",
        "stale",
    ]
    assert all(candidate.source == "trending" for candidate in ranked)


def test_blend_ranked_candidates_deduplicates_and_fills_page() -> None:
    primary = [
        SimpleNamespace(product_id="p1"),
        SimpleNamespace(product_id="p2"),
        SimpleNamespace(product_id="p3"),
    ]
    secondary = [
        SimpleNamespace(product_id="p2"),
        SimpleNamespace(product_id="t1"),
        SimpleNamespace(product_id="t2"),
    ]

    blended = FeedService._blend_ranked_candidates(
        primary=primary,
        secondary=secondary,
        page_size=4,
        primary_target=2,
    )

    assert [candidate.product_id for candidate in blended] == ["p1", "t1", "p2", "t2"]


@pytest.mark.asyncio
async def test_generate_feed_without_vector_uses_trending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = make_service()
    expected_candidates = [
        SimpleNamespace(product_id="t1", score=0.9, source="trending"),
    ]

    async def fake_load_user_vector(user_id: str) -> None:
        assert user_id == "user-1"
        return None

    async def fake_load_user_profile_state(user_id: str, session: object) -> object:
        return SimpleNamespace(profile_confidence=0.0)

    async def fake_get_interacted_product_ids(
        user_id: str, session: object
    ) -> set[str]:
        return set()

    async def fake_generate_trending_feed(**kwargs) -> list[SimpleNamespace]:
        assert kwargs["seen_ids"] == []
        assert kwargs["category"] is None
        assert kwargs["page_size"] == 20
        return expected_candidates

    monkeypatch.setattr(service, "_load_user_vector", fake_load_user_vector)
    monkeypatch.setattr(
        service,
        "_load_user_profile_state",
        fake_load_user_profile_state,
    )
    monkeypatch.setattr(
        service,
        "_get_interacted_product_ids",
        fake_get_interacted_product_ids,
    )
    monkeypatch.setattr(service, "_generate_trending_feed", fake_generate_trending_feed)

    result = await service.generate_feed(
        user_id="user-1",
        seen_ids=[],
        session=object(),
        page_size=20,
    )

    assert result.feed_mode is FeedMode.TRENDING
    assert result.candidates == expected_candidates
