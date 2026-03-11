from types import SimpleNamespace

import pytest

from src.features.clustering.service.cold_start_service import ColdStartService
from src.features.clustering.schemas.schemas import ColdStartMatch


def make_service() -> ColdStartService:
    return ColdStartService(
        qdrant_client=None,
        settings=SimpleNamespace(
            qdrant_collection="products",
            cluster_collection="style_clusters",
        ),
    )


def test_to_matches_deduplicates_and_respects_exclusions() -> None:
    matches = ColdStartService._to_matches(
        products=[
            {"product_id": "p1", "score": 0.95, "cluster_index": 1},
            {"product_id": "p1", "score": 0.94, "cluster_index": 1},
            {"product_id": "p2", "score": 0.93, "cluster_index": 2},
            {"product_id": "p3", "score": 0.92, "cluster_index": 3},
        ],
        limit=2,
        is_diversity=False,
        exclude_ids={"blocked"},
    )

    assert [match.product_id for match in matches] == ["p1", "p2"]
    assert all(match.is_diversity is False for match in matches)


def test_interleave_diversity_spreads_items_through_feed() -> None:
    primary_matches = [
        ColdStartMatch(product_id="p1", score=0.99, cluster_index=1),
        ColdStartMatch(product_id="p2", score=0.98, cluster_index=1),
        ColdStartMatch(product_id="p3", score=0.97, cluster_index=2),
        ColdStartMatch(product_id="p4", score=0.96, cluster_index=2),
    ]
    diversity_matches = [
        ColdStartMatch(product_id="d1", score=0.8, cluster_index=4, is_diversity=True),
        ColdStartMatch(product_id="d2", score=0.79, cluster_index=5, is_diversity=True),
    ]

    merged = ColdStartService._interleave_diversity(primary_matches, diversity_matches)

    assert [match.product_id for match in merged] == ["p1", "p2", "d1", "p3", "p4", "d2"]


@pytest.mark.asyncio
async def test_find_nearest_clusters_uses_query_points_response_shape() -> None:
    class FakeQdrantClient:
        async def query_points(self, **kwargs):
            assert kwargs["collection_name"] == "style_clusters"
            assert kwargs["query"] == [0.5, 0.5]
            assert kwargs["limit"] == 3
            return SimpleNamespace(
                points=[
                    SimpleNamespace(
                        id=11,
                        score=0.91,
                        payload={"cluster_index": 7, "product_count": 12},
                    )
                ]
            )

    service = ColdStartService(
        qdrant_client=FakeQdrantClient(),
        settings=SimpleNamespace(
            qdrant_collection="products",
            cluster_collection="style_clusters",
        ),
    )

    clusters = await service.find_nearest_clusters(
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
        top_k=3,
    )

    assert clusters == [{"cluster_index": 7, "score": 0.91, "product_count": 12}]


@pytest.mark.asyncio
async def test_get_cold_start_feed_prefers_similarity_ranked_hits_and_fills_gaps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = make_service()

    async def fake_find_nearest_clusters(
        embeddings: list[list[float]], top_k: int = 5
    ) -> list[dict]:
        assert embeddings
        assert top_k == 5
        return [
            {"cluster_index": 1, "score": 0.98, "product_count": 10},
            {"cluster_index": 2, "score": 0.95, "product_count": 10},
            {"cluster_index": 3, "score": 0.93, "product_count": 10},
            {"cluster_index": 4, "score": 0.88, "product_count": 10},
            {"cluster_index": 5, "score": 0.85, "product_count": 10},
        ]

    async def fake_search_products(
        query_vector: list[float],
        limit: int,
        cluster_indices: list[int] | None = None,
    ) -> list[dict]:
        assert query_vector
        assert limit >= 6
        if cluster_indices == [1, 2, 3]:
            return [
                {"product_id": "p1", "score": 0.99, "cluster_index": 1},
                {"product_id": "p2", "score": 0.98, "cluster_index": 2},
                {"product_id": "p3", "score": 0.97, "cluster_index": 3},
            ]
        if cluster_indices == [4, 5]:
            return [
                {"product_id": "p1", "score": 0.96, "cluster_index": 4},
                {"product_id": "d1", "score": 0.95, "cluster_index": 4},
                {"product_id": "d2", "score": 0.94, "cluster_index": 5},
            ]
        return [{"product_id": "fill-1", "score": 0.9, "cluster_index": 8}]

    monkeypatch.setattr(service, "find_nearest_clusters", fake_find_nearest_clusters)
    monkeypatch.setattr(service, "_search_products", fake_search_products)

    response = await service.get_cold_start_feed(
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
        feed_size=6,
    )

    assert response.primary_clusters == [1, 2, 3]
    assert response.diversity_clusters == [4, 5]
    assert response.total_matches == 6
    assert [match.product_id for match in response.matches] == [
        "p1",
        "p2",
        "d1",
        "p3",
        "d2",
        "fill-1",
    ]
    assert [match.is_diversity for match in response.matches] == [
        False,
        False,
        True,
        False,
        True,
        False,
    ]
