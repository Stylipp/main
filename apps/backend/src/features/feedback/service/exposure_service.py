"""Exposure logging for visible feed cards and completed actions."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.feedback.schemas.schemas import ExposureEvent
from src.models.exposure_log import ExposureLog
from src.models.product import Product

logger = logging.getLogger(__name__)


class ExposureService:
    """Persist and merge feed exposure events."""

    async def record_exposures(
        self,
        user_id: UUID,
        events: list[ExposureEvent],
        session: AsyncSession,
    ) -> int:
        """Insert or update exposure rows for a batch of events."""
        product_ids = self._coerce_product_ids([event.product_id for event in events])
        if not product_ids:
            return 0

        valid_products = await self._load_products(session, product_ids)
        if not valid_products:
            return 0

        existing_rows = await self._load_existing_rows(
            session,
            user_id=user_id,
            session_ids=list({event.session_id for event in events}),
            product_ids=list(valid_products),
        )
        existing_by_key = {
            self._row_key(row.session_id, row.product_id): row for row in existing_rows
        }

        processed = 0
        for event in events:
            product_id = self._coerce_product_id(event.product_id)
            if product_id is None or product_id not in valid_products:
                continue

            key = self._row_key(event.session_id, product_id)
            row = existing_by_key.get(key)
            if row is None:
                row = ExposureLog(
                    user_id=user_id,
                    product_id=product_id,
                    session_id=event.session_id,
                    feed_mode=event.feed_mode.value,
                    position=event.position,
                    shown_at=self._to_utc(event.shown_at),
                )
                session.add(row)
                existing_by_key[key] = row

            self._apply_event(row, event)
            processed += 1

        await session.commit()
        return processed

    async def _load_products(
        self,
        session: AsyncSession,
        product_ids: list[UUID],
    ) -> set[UUID]:
        stmt = select(Product.id).where(Product.id.in_(product_ids))
        result = await session.execute(stmt)
        return {row.id for row in result.all()}

    async def _load_existing_rows(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        session_ids: list[str],
        product_ids: list[UUID],
    ) -> list[ExposureLog]:
        stmt = select(ExposureLog).where(
            ExposureLog.user_id == user_id,
            ExposureLog.session_id.in_(session_ids),
            ExposureLog.product_id.in_(product_ids),
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def _apply_event(row: ExposureLog, event: ExposureEvent) -> None:
        event_shown_at = ExposureService._to_utc(event.shown_at)
        if event_shown_at < row.shown_at:
            row.shown_at = event_shown_at
        row.position = min(row.position, event.position)

        if event.action is None:
            return

        event_action_at = ExposureService._to_utc(event.action_at)
        if row.action_at is None or event_action_at >= row.action_at:
            row.action = event.action.value
            row.action_at = event_action_at

        if event.dwell_ms is not None:
            row.dwell_ms = max(row.dwell_ms or 0, event.dwell_ms)

    @staticmethod
    def _row_key(session_id: str, product_id: UUID) -> tuple[str, UUID]:
        return session_id, product_id

    @staticmethod
    def _coerce_product_ids(product_ids: list[str]) -> list[UUID]:
        parsed: list[UUID] = []
        for product_id in product_ids:
            parsed_id = ExposureService._coerce_product_id(product_id)
            if parsed_id is not None:
                parsed.append(parsed_id)
        return parsed

    @staticmethod
    def _coerce_product_id(product_id: str) -> UUID | None:
        try:
            return UUID(product_id)
        except ValueError:
            logger.warning("Skipping invalid exposure product_id=%s", product_id)
            return None

    @staticmethod
    def _to_utc(value: datetime | None) -> datetime:
        if value is None:
            return datetime.now(timezone.utc)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
