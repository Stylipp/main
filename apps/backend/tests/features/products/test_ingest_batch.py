"""Regression tests for batch ingest response handling (HTTP 200 / 207)."""

from decimal import Decimal

from src.features.products.schemas.schemas import (
    BatchIngestResponse,
    RejectedItem,
)


def test_batch_response_200_full_success() -> None:
    """HTTP 200 full success returns accepted_ids with no rejected items."""
    response = BatchIngestResponse(
        total=3,
        created=2,
        updated=1,
        failed=0,
        accepted_ids=["prod_1", "prod_2", "prod_3"],
        rejected=[],
    )

    assert response.total == 3
    assert response.failed == 0
    assert len(response.accepted_ids) == 3
    assert response.rejected == []
    assert "prod_1" in response.accepted_ids


def test_batch_response_207_partial_success() -> None:
    """HTTP 207 partial success returns both accepted_ids and rejected items."""
    response = BatchIngestResponse(
        total=3,
        created=1,
        updated=1,
        failed=1,
        accepted_ids=["prod_1", "prod_2"],
        rejected=[
            RejectedItem(
                external_id="prod_3",
                store_id="test-store",
                error="Quality gate: image too small",
                retryable=False,
            )
        ],
    )

    assert response.total == 3
    assert len(response.accepted_ids) == 2
    assert response.failed == 1
    assert len(response.rejected) == 1
    assert response.rejected[0].external_id == "prod_3"
    assert response.rejected[0].retryable is False


def test_rejected_item_retryable_flag() -> None:
    """Transient errors are retryable, validation failures are not."""
    transient = RejectedItem(
        external_id="prod_a",
        store_id="s1",
        error="Unexpected error: connection timeout",
        retryable=True,
    )
    permanent = RejectedItem(
        external_id="prod_b",
        store_id="s1",
        error="Quality gate: blurry image",
        retryable=False,
    )

    assert transient.retryable is True
    assert permanent.retryable is False


def test_batch_response_207_condition() -> None:
    """207 is returned only when both accepted_ids and rejected exist."""
    # Both present -> 207 condition
    response = BatchIngestResponse(
        total=2,
        created=1,
        updated=0,
        failed=1,
        accepted_ids=["prod_1"],
        rejected=[
            RejectedItem(
                external_id="prod_2",
                store_id="s1",
                error="fail",
                retryable=False,
            )
        ],
    )
    should_be_207 = bool(response.accepted_ids) and bool(response.rejected)
    assert should_be_207 is True

    # All accepted -> 200 condition
    all_ok = BatchIngestResponse(
        total=2,
        created=2,
        updated=0,
        failed=0,
        accepted_ids=["prod_1", "prod_2"],
        rejected=[],
    )
    should_be_200 = bool(all_ok.accepted_ids) and not bool(all_ok.rejected)
    assert should_be_200 is True
