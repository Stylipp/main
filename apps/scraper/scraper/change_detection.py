"""SQLite-based change detection — tracks content hashes between runs."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import aiosqlite

from .schemas import ChangeReport, ScrapedProduct

_DEFAULT_DB = Path(__file__).parent.parent / "data" / "scraper_state.db"


class ChangeDetector:
    def __init__(self, db_path: str | Path = _DEFAULT_DB) -> None:
        self.db_path = str(db_path)

    async def initialize(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
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
                )
            """)
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_store ON product_hashes (store_id)"
            )
            await db.commit()

    @staticmethod
    def compute_hash(product: ScrapedProduct) -> str:
        parts = [
            product.title,
            str(product.price) if product.price else "",
            str(product.sale_price) if product.sale_price else "",
            product.currency,
            (product.description or "")[:500],
            "|".join(sorted(product.image_urls)),
        ]
        return hashlib.sha256("|".join(parts).encode()).hexdigest()

    async def detect_changes(
        self, store_id: str, products: list[ScrapedProduct]
    ) -> ChangeReport:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT external_id, content_hash FROM product_hashes WHERE store_id = ?",
                (store_id,),
            )
            existing = {row[0]: row[1] async for row in cursor}

        new, changed, unchanged = [], [], 0
        seen_ids = set()

        for p in products:
            seen_ids.add(p.external_id)
            h = self.compute_hash(p)
            if p.external_id not in existing:
                new.append(p)
            elif existing[p.external_id] != h:
                changed.append(p)
            else:
                unchanged += 1

        removed_ids = [eid for eid in existing if eid not in seen_ids]

        return ChangeReport(
            store_id=store_id,
            new=new,
            changed=changed,
            removed_ids=removed_ids,
            unchanged_count=unchanged,
        )

    async def update_hashes(self, store_id: str, products: list[ScrapedProduct]) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            for p in products:
                h = self.compute_hash(p)
                await db.execute(
                    """INSERT INTO product_hashes
                       (store_id, external_id, url, content_hash, title, price, image_url)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(store_id, external_id) DO UPDATE SET
                         url=excluded.url,
                         content_hash=excluded.content_hash,
                         title=excluded.title,
                         price=excluded.price,
                         image_url=excluded.image_url,
                         last_seen_at=datetime('now'),
                         last_changed_at=datetime('now')
                    """,
                    (
                        store_id,
                        p.external_id,
                        p.url,
                        h,
                        p.title,
                        str(p.price) if p.price else None,
                        p.image_urls[0] if p.image_urls else None,
                    ),
                )
            await db.commit()

    async def mark_removed(self, store_id: str, external_ids: list[str]) -> None:
        if not external_ids:
            return
        async with aiosqlite.connect(self.db_path) as db:
            placeholders = ",".join("?" for _ in external_ids)
            await db.execute(
                f"DELETE FROM product_hashes WHERE store_id = ? AND external_id IN ({placeholders})",
                [store_id, *external_ids],
            )
            await db.commit()
