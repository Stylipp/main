---
phase: 17-scraper-hardening
plan: 02
subsystem: api
tags: [sqlalchemy, qdrant, soft-delete, archival, fastapi]

# Dependency graph
requires:
  - phase: 17-01
    provides: per-product sync contract with accepted_ids/rejected arrays
  - phase: 02
    provides: Product model, IngestionService, Qdrant storage
provides:
  - archived_at column on Product model for soft-delete
  - archive_products service method (PostgreSQL + Qdrant payload)
  - POST /api/products/archive/batch endpoint
affects: [feed-generation, scraper-orchestrator]

# Tech tracking
tech-stack:
  added: []
  patterns: [soft-delete via nullable timestamp + Qdrant payload flag]

key-files:
  created:
    - apps/backend/alembic/versions/2026_04_19_0001-f6a7b8c9d0e1_add_archived_at_to_products.py
  modified:
    - apps/backend/src/models/product.py
    - apps/backend/src/features/products/service/ingestion_service.py
    - apps/backend/src/features/products/router/router.py
    - apps/backend/src/features/products/schemas/schemas.py

key-decisions:
  - "Soft-delete via nullable archived_at timestamp — NULL means active, non-NULL means archived"
  - "Qdrant payload flag {archived: True} via set_payload — no hard-delete of points"
  - "archive_products accepts session parameter for caller-controlled commit"

patterns-established:
  - "Soft-delete pattern: archived_at timestamp + Qdrant payload flag, no hard-delete"

issues-created: []

# Metrics
duration: 3min
completed: 2026-04-19
---

# Phase 17 Plan 02: Product Archival Summary

**Soft-delete archival via archived_at timestamp in PostgreSQL and archived=True payload flag in Qdrant, with batch archive endpoint**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-19T19:39:59Z
- **Completed:** 2026-04-19T19:42:37Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Product model extended with nullable `archived_at` DateTime column + index
- Alembic migration for the new column
- `archive_products` service method: sets `archived_at` in PostgreSQL and `archived: True` in Qdrant payload
- `POST /api/products/archive/batch` endpoint with BatchArchiveRequest/Response schemas

## Task Commits

Each task was committed atomically:

1. **Task 1: Add archived_at column to Product model** - `4937108` (feat)
2. **Task 2: Add batch archive endpoint with soft-delete** - `f3819a1` (feat)

## Files Created/Modified
- `apps/backend/src/models/product.py` - Added archived_at field and index
- `apps/backend/alembic/versions/2026_04_19_0001-f6a7b8c9d0e1_add_archived_at_to_products.py` - Migration for archived_at column
- `apps/backend/src/features/products/schemas/schemas.py` - BatchArchiveRequest/Response schemas
- `apps/backend/src/features/products/service/ingestion_service.py` - archive_products method
- `apps/backend/src/features/products/router/router.py` - POST /archive/batch endpoint

## Decisions Made
- Soft-delete via nullable `archived_at` timestamp (NULL = active, non-NULL = archived)
- Qdrant points get `{archived: True}` payload via `set_payload` — no hard-delete preserves interaction history
- `archive_products` method takes session as parameter so the router controls commit timing

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Archival endpoint ready for scraper orchestrator integration
- Feed generation can filter by `archived_at IS NULL` and Qdrant `archived` payload field
- Ready for next plan in Phase 17

---
*Phase: 17-scraper-hardening*
*Completed: 2026-04-19*
