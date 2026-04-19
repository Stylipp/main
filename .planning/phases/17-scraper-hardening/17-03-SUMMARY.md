---
phase: 17-scraper-hardening
plan: 03
subsystem: feed, ingestion
tags: [qdrant, feed-filter, archival, payload-index]

# Dependency graph
requires:
  - phase: 17-02
    provides: archived_at column on Product, Qdrant archived payload flag, archive_products method
provides:
  - Feed queries exclude archived products via Qdrant must_not filter
  - Qdrant payload index on archived field for filter performance
  - Automatic un-archival of returning products during ingestion
affects: [feed, scraper-sync]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Qdrant payload index creation at app startup (idempotent)"
    - "Un-archive pattern: clear archived_at + set Qdrant payload before update"

key-files:
  created: []
  modified:
    - apps/backend/src/features/feed/service/feed_service.py
    - apps/backend/src/features/products/service/ingestion_service.py
    - apps/backend/src/core/qdrant.py
    - apps/backend/src/main.py

key-decisions:
  - "Archived filter placed as first must_not condition, always applied regardless of other filters"
  - "Payload index created idempotently at app startup via ensure_products_payload_indexes()"
  - "Un-archive clears archived_at and Qdrant flag before calling _update_existing to also refresh metadata"

patterns-established:
  - "ensure_*_payload_indexes() pattern for Qdrant index management at startup"

issues-created: []

# Metrics
duration: 2min
completed: 2026-04-19
---

# Phase 17 Plan 3: Feed Archival Filter & Un-archive Summary

**Feed queries now exclude archived products via Qdrant must_not filter with payload index; returning products are automatically un-archived during ingestion**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-19T19:48:48Z
- **Completed:** 2026-04-19T19:50:38Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Feed `_build_candidate_filter` always excludes `archived=True` products via must_not condition
- Qdrant payload index on `archived` field created at app startup for filter performance
- `ingest_or_update_product` detects archived products and clears `archived_at` + Qdrant `archived` flag before updating metadata

## Task Commits

Each task was committed atomically:

1. **Task 1: Add archived filter to feed Qdrant queries + create payload index** - `c84d5bd` (feat)
2. **Task 2: Un-archive returning products in ingest_or_update_product** - `1cc0f79` (feat)

**Plan metadata:** (pending)

## Files Created/Modified
- `apps/backend/src/features/feed/service/feed_service.py` - Added archived must_not filter in _build_candidate_filter
- `apps/backend/src/features/products/service/ingestion_service.py` - Added un-archive logic before _update_existing
- `apps/backend/src/core/qdrant.py` - Added ensure_products_payload_indexes() with archived bool index
- `apps/backend/src/main.py` - Call ensure_products_payload_indexes() at startup

## Decisions Made
- Archived filter placed as first must_not condition — always applied regardless of exclude_seen or apply_price settings
- Payload index created idempotently at app startup via dedicated function in qdrant.py
- Un-archive happens before _update_existing so metadata also gets refreshed in the same flow

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Archived products fully excluded from feed pipeline
- Re-listed products handled gracefully (un-archived, not duplicated)
- Ready for next 17-XX plan

---
*Phase: 17-scraper-hardening*
*Completed: 2026-04-19*
