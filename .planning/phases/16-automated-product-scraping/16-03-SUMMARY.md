---
phase: 16-automated-product-scraping
plan: 03
subsystem: api
tags: [sqlite, change-detection, hashing, scraper, aiosqlite]

# Dependency graph
requires:
  - phase: 16-01
    provides: ScrapedProduct schema, scraper feature folder structure, scraper_sqlite_path config
provides:
  - ChangeDetectionService with SQLite persistence and content hashing
  - ChangeReport dataclass for new/changed/removed/unchanged classification
  - Deterministic SHA-256 content hashing (excludes volatile fields)
  - UPSERT-based hash persistence with first_seen_at preservation
  - Parameterized SQL queries (no injection risk)
affects: [16-04, scraper-sync, scraper-scheduler]

# Tech tracking
tech-stack:
  added: [aiosqlite]
  patterns: [SQLite async via aiosqlite, content hashing for change detection, UPSERT with ON CONFLICT]

key-files:
  created:
    - apps/backend/src/features/scraper/service/change_detection.py
  modified:
    - apps/backend/pyproject.toml

key-decisions:
  - "SHA-256 content hash from title, price, sale_price, currency, description[:500], sorted image_urls"
  - "Excluded scraped_at and store_id from hash (volatile, not product changes)"
  - "ON CONFLICT UPSERT preserves first_seen_at, conditionally updates last_changed_at"
  - "Each method opens its own aiosqlite connection (async context manager pattern)"
  - "Parameterized placeholders for mark_removed IN clause (SQL injection prevention)"

patterns-established:
  - "Async SQLite service pattern: each method uses async with aiosqlite.connect()"
  - "Dataclass for internal reports (ChangeReport) vs Pydantic for API schemas"

issues-created: []

# Metrics
duration: 5min
completed: 2026-03-18
---

# Phase 16-03: Change Detection Summary

**SQLite-based change detection engine with deterministic content hashing and diff calculation**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-18
- **Completed:** 2026-03-18
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- ChangeDetectionService with SQLite schema initialization (product_hashes table with composite PK, store_id index)
- Deterministic SHA-256 content hashing that excludes volatile fields (scraped_at, store_id) to avoid false change detections
- Full diff calculation: detect_changes() classifies products as new, changed, unchanged, or removed
- UPSERT-based update_hashes() preserves first_seen_at while updating last_seen_at and conditionally updating last_changed_at
- mark_removed() with parameterized IN clause for safe bulk deletion
- get_store_stats() for monitoring (total, oldest, newest)
- ChangeReport dataclass for structured diff results
- aiosqlite>=0.20.0 added to pyproject.toml dependencies

## Task Commits

Each task was committed atomically:

1. **Task 1: Create content hashing for scraped products** - `fad39d6` (feat)
2. **Task 2: Implement diff calculation** - included in `fad39d6` (same file, complete implementation)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified
- `apps/backend/src/features/scraper/service/change_detection.py` - ChangeDetectionService class with initialize(), compute_hash(), detect_changes(), update_hashes(), mark_removed(), get_store_stats() + ChangeReport dataclass
- `apps/backend/pyproject.toml` - Added aiosqlite>=0.20.0 to dependencies

## Decisions Made
- Used SHA-256 over MD5 for content hashing (stronger collision resistance, plan spec)
- Canonical hash string built from: title, price (str), sale_price (str), currency, description[:500], sorted image_urls joined with |
- UPSERT pattern uses `ON CONFLICT(store_id, external_id) DO UPDATE SET` with conditional last_changed_at update only when hash actually differs
- Each async method opens/closes its own aiosqlite connection for simplicity (no connection pooling needed for nightly batch)
- mark_removed uses dynamically generated placeholder string with parameterized values (not string interpolation)

## Deviations from Plan

- Both tasks were implemented in a single file write and committed together since they target the same file. All verification criteria for both tasks pass independently.

## Issues Encountered
None.

## Next Phase Readiness
- ChangeDetectionService ready for integration with scraper pipeline orchestrator
- detect_changes() can be called after each store scrape to determine sync workload
- update_hashes() should be called after successful WooCommerce/DB/Qdrant sync
- mark_removed() handles cleanup of products no longer in store sitemaps
- SQLite DB path controlled by Settings.scraper_sqlite_path

---
*Phase: 16-automated-product-scraping*
*Completed: 2026-03-18*
