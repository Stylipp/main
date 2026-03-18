"""Change detection service for scraped product data.

Uses SQLite to track content hashes and identify new, changed, and removed
products between scrape runs. Avoids re-processing unchanged products.
"""

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

import aiosqlite

from src.features.scraper.schemas.schemas import ScrapedProduct


@dataclass
class ChangeReport:
    """Result of comparing scraped products against stored hashes."""

    store_id: str
    new: list[ScrapedProduct] = field(default_factory=list)
    changed: list[ScrapedProduct] = field(default_factory=list)
    removed_ids: list[str] = field(default_factory=list)
    unchanged_count: int = 0


class ChangeDetectionService:
    """Tracks product content hashes in SQLite to detect changes between scrape runs."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    async def initialize(self) -> None:
        """Create SQLite database and schema if not exists."""
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS product_hashes (
                    store_id TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    title TEXT,
                    price TEXT,
                    image_url TEXT,
                    first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
                    last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
                    last_changed_at TEXT NOT NULL DEFAULT (datetime('now')),
                    PRIMARY KEY (store_id, external_id)
                );
            """
            )
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_product_hashes_store_id
                ON product_hashes (store_id);
            """
            )
            await db.commit()

    @staticmethod
    def compute_hash(product: ScrapedProduct) -> str:
        """Compute a deterministic content hash from product fields.

        Excludes volatile fields (scraped_at, store_id) that change every run
        but don't indicate actual product changes.
        """
        # Build canonical string from fields that matter for change detection
        parts = [
            product.title,
            str(product.price) if product.price is not None else "",
            str(product.sale_price) if product.sale_price is not None else "",
            product.currency,
            (product.description or "")[:500],
            "|".join(sorted(product.image_urls)),
        ]
        canonical = "\n".join(parts)
        return hashlib.sha256(canonical.encode()).hexdigest()

    async def detect_changes(
        self, store_id: str, products: list[ScrapedProduct]
    ) -> ChangeReport:
        """Compare scraped products against stored hashes to detect changes.

        Classifies each product as new, changed, or unchanged, and identifies
        products that have been removed from the store.
        """
        report = ChangeReport(store_id=store_id)

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT external_id, content_hash FROM product_hashes WHERE store_id = ?",
                (store_id,),
            )
            rows = await cursor.fetchall()
            existing = {row[0]: row[1] for row in rows}

        scraped_ids: set[str] = set()

        for product in products:
            scraped_ids.add(product.external_id)
            current_hash = self.compute_hash(product)

            if product.external_id not in existing:
                report.new.append(product)
            elif existing[product.external_id] != current_hash:
                report.changed.append(product)
            else:
                report.unchanged_count += 1

        # Products in DB but not in current scrape are removed
        for ext_id in existing:
            if ext_id not in scraped_ids:
                report.removed_ids.append(ext_id)

        return report

    async def update_hashes(
        self, store_id: str, products: list[ScrapedProduct]
    ) -> None:
        """Persist content hashes for scraped products after successful sync.

        Uses UPSERT to insert new products and update changed ones while
        preserving first_seen_at for existing products.
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        async with aiosqlite.connect(self.db_path) as db:
            for product in products:
                content_hash = self.compute_hash(product)
                first_image = product.image_urls[0] if product.image_urls else None
                price_str = str(product.price) if product.price is not None else None

                await db.execute(
                    """
                    INSERT INTO product_hashes
                        (store_id, external_id, url, content_hash, title, price,
                         image_url, first_seen_at, last_seen_at, last_changed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(store_id, external_id) DO UPDATE SET
                        url = excluded.url,
                        content_hash = excluded.content_hash,
                        title = excluded.title,
                        price = excluded.price,
                        image_url = excluded.image_url,
                        last_seen_at = excluded.last_seen_at,
                        last_changed_at = CASE
                            WHEN product_hashes.content_hash != excluded.content_hash
                            THEN excluded.last_changed_at
                            ELSE product_hashes.last_changed_at
                        END
                    """,
                    (
                        store_id,
                        product.external_id,
                        product.url,
                        content_hash,
                        product.title,
                        price_str,
                        first_image,
                        now,
                        now,
                        now,
                    ),
                )
            await db.commit()

    async def mark_removed(self, store_id: str, external_ids: list[str]) -> None:
        """Delete removed products from the hash table.

        Uses parameterized queries to prevent SQL injection.
        """
        if not external_ids:
            return

        placeholders = ",".join("?" for _ in external_ids)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"DELETE FROM product_hashes WHERE store_id = ? AND external_id IN ({placeholders})",
                (store_id, *external_ids),
            )
            await db.commit()

    async def get_store_stats(self, store_id: str) -> dict:
        """Return summary statistics for a store's tracked products.

        Returns:
            Dict with total count, oldest and newest first_seen_at timestamps.
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT
                    COUNT(*) as total,
                    MIN(first_seen_at) as oldest,
                    MAX(first_seen_at) as newest
                FROM product_hashes
                WHERE store_id = ?
                """,
                (store_id,),
            )
            row = await cursor.fetchone()

        if row and row[0] > 0:
            return {"total": row[0], "oldest": row[1], "newest": row[2]}
        return {"total": 0, "oldest": None, "newest": None}
