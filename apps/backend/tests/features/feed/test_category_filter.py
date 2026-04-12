from qdrant_client.models import FieldCondition, MatchValue

from src.features.feed.service.feed_service import FeedService


def test_build_candidate_filter_includes_category_condition() -> None:
    query_filter = FeedService._build_candidate_filter(
        seen_ids=[],
        price_min=0.0,
        price_max=0.0,
        category="shoes",
    )

    assert query_filter is not None
    assert query_filter.must is not None

    category_conditions = [condition for condition in query_filter.must if isinstance(condition, FieldCondition)]
    assert len(category_conditions) == 1
    assert category_conditions[0].key == "category"
    assert isinstance(category_conditions[0].match, MatchValue)
    assert category_conditions[0].match.value == "shoes"
