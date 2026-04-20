from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.features.feedback.schemas.schemas import (
    ExposureEvent,
    FeedbackAction,
)
from src.features.feedback.service.exposure_service import ExposureService
from src.features.feed.schemas.schemas import FeedMode
from src.models.exposure_log import ExposureLog


def make_event(
    *,
    product_id: str,
    session_id: str,
    shown_at: datetime,
    position: int = 1,
    action: FeedbackAction | None = None,
    action_at: datetime | None = None,
    dwell_ms: int | None = None,
) -> ExposureEvent:
    return ExposureEvent(
        product_id=product_id,
        session_id=session_id,
        feed_mode=FeedMode.TRENDING,
        position=position,
        shown_at=shown_at,
        action=action,
        action_at=action_at,
        dwell_ms=dwell_ms,
    )


def test_apply_event_merges_earliest_shown_and_action_completion() -> None:
    row = ExposureLog(
        user_id=uuid4(),
        product_id=uuid4(),
        session_id="session-1",
        feed_mode="trending",
        position=5,
        shown_at=datetime(2026, 4, 19, 11, 30, tzinfo=timezone.utc),
    )
    event = make_event(
        product_id=str(row.product_id),
        session_id=row.session_id,
        position=2,
        shown_at=datetime(2026, 4, 19, 11, 25, tzinfo=timezone.utc),
        action=FeedbackAction.LIKE,
        action_at=datetime(2026, 4, 19, 11, 35, tzinfo=timezone.utc),
        dwell_ms=8_000,
    )

    ExposureService._apply_event(row, event)

    assert row.shown_at == event.shown_at
    assert row.position == 2
    assert row.action == "like"
    assert row.action_at == event.action_at
    assert row.dwell_ms == 8_000


def test_apply_event_keeps_latest_action_timestamp() -> None:
    row = ExposureLog(
        user_id=uuid4(),
        product_id=uuid4(),
        session_id="session-1",
        feed_mode="hybrid",
        position=1,
        shown_at=datetime(2026, 4, 19, 11, 30, tzinfo=timezone.utc),
        action="save",
        action_at=datetime(2026, 4, 19, 11, 40, tzinfo=timezone.utc),
        dwell_ms=9_000,
    )
    event = make_event(
        product_id=str(row.product_id),
        session_id=row.session_id,
        position=3,
        shown_at=datetime(2026, 4, 19, 11, 32, tzinfo=timezone.utc),
        action=FeedbackAction.DISLIKE,
        action_at=datetime(2026, 4, 19, 11, 38, tzinfo=timezone.utc),
        dwell_ms=12_000,
    )

    ExposureService._apply_event(row, event)

    assert row.position == 1
    assert row.action == "save"
    assert row.action_at == datetime(2026, 4, 19, 11, 40, tzinfo=timezone.utc)
    assert row.dwell_ms == 12_000


@pytest.mark.asyncio
async def test_record_exposures_merges_multiple_events_into_one_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = ExposureService()
    user_id = uuid4()
    product_id = uuid4()
    shown_at = datetime.now(timezone.utc)
    action_at = shown_at + timedelta(seconds=6)
    added_rows: list[ExposureLog] = []
    commit_count = 0

    class FakeSession:
        def add(self, row: ExposureLog) -> None:
            added_rows.append(row)

        async def commit(self) -> None:
            nonlocal commit_count
            commit_count += 1

    async def fake_load_products(session, product_ids):
        assert product_ids == [product_id, product_id]
        return {product_id}

    async def fake_load_existing_rows(session, **kwargs):
        return []

    monkeypatch.setattr(service, "_load_products", fake_load_products)
    monkeypatch.setattr(service, "_load_existing_rows", fake_load_existing_rows)

    processed = await service.record_exposures(
        user_id=user_id,
        events=[
            make_event(
                product_id=str(product_id),
                session_id="session-1",
                shown_at=shown_at,
                position=4,
            ),
            make_event(
                product_id=str(product_id),
                session_id="session-1",
                shown_at=shown_at,
                position=4,
                action=FeedbackAction.LIKE,
                action_at=action_at,
                dwell_ms=6_000,
            ),
        ],
        session=FakeSession(),
    )

    assert processed == 2
    assert commit_count == 1
    assert len(added_rows) == 1
    assert added_rows[0].action == "like"
    assert added_rows[0].action_at == action_at
    assert added_rows[0].dwell_ms == 6_000


@pytest.mark.asyncio
async def test_record_exposures_skips_invalid_product_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = ExposureService()
    session = SimpleNamespace(commit=None)

    async def fake_commit() -> None:
        raise AssertionError("commit should not be called when nothing is processed")

    session.commit = fake_commit

    async def fake_load_products(session, product_ids):
        raise AssertionError("should not load products for invalid ids")

    monkeypatch.setattr(service, "_load_products", fake_load_products)

    processed = await service.record_exposures(
        user_id=uuid4(),
        events=[
            make_event(
                product_id="not-a-uuid",
                session_id="session-1",
                shown_at=datetime.now(timezone.utc),
            )
        ],
        session=session,
    )

    assert processed == 0
