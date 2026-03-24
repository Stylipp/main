from datetime import datetime, timezone
from types import SimpleNamespace

from src.features.feed.service.feed_service import FeedService


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
