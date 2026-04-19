---
phase: 17-scraper-hardening
plan: 04
subsystem: scraper
tags: [sqlite, httpx, soft-delete, change-detection, backend-sync]

# Dependency graph
requires:
  - phase: 17-01
    provides: Per-product sync contract with accepted_ids in response
  - phase: 17-02
    provides: Backend POST /archive/batch endpoint
provides:
  - Selective hash updates based on backend acceptance (failed products retried)
  - Soft-delete in SQLite change detection (removed_at instead of DELETE)
  - Backend archive notification for removed products
  - Returning product detection (re-appeared after removal)
affects: [scraper-pipeline, product-lifecycle]

# Tech tracking
tech-stack:
  added: []
  patterns: [selective-sync, soft-delete-tracking, returning-product-detection]

key-files:
  created: []
  modified:
    - apps/scraper/scraper/backend_sync.py
    - apps/scraper/scraper/schemas.py
    - apps/scraper/scraper/pipeline.py
    - apps/scraper/scraper/change_detection.py

key-decisions:
  - "SyncResult dataclass in schemas.py for push/update return type"
  - "Soft-delete via removed_at TEXT column with ALTER TABLE migration for existing DBs"
  - "Returning products (re-appeared after removal) treated as changed, not new"
  - "Selective hash update: only accepted_ids get their hashes updated in SQLite"

patterns-established:
  - "Selective sync: only update local state for backend-accepted items"
  - "Soft-delete tracking: removed_at timestamp preserves history, enables return detection"

issues-created: []

# Metrics
duration: 2min
completed: 2026-04-19
---

# Phase 17 Plan 04: Selective Hash Updates & Soft-Delete Summary

**SyncResult with accepted_ids for selective hash updates, SQLite soft-delete via removed_at, and backend archive notification for removed products**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-19T19:56:40Z
- **Completed:** 2026-04-19T19:58:45Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- push_products and update_products now return SyncResult with accepted_ids — pipeline only updates SQLite hashes for accepted products
- Failed/rejected products keep old hash and are automatically retried on next scraper run
- mark_removed uses soft-delete (removed_at timestamp) instead of hard DELETE
- detect_changes excludes soft-deleted rows and detects returning products (re-appeared after removal)
- Pipeline calls sync.archive_products to notify backend when products are removed from source

## Task Commits

Each task was committed atomically:

1. **Task 1: Update BackendSync to return accepted_ids and call archive endpoint** - `dc144e3` (feat)
2. **Task 2: Selective hash update + soft-delete mark_removed + archive call in pipeline** - `81ff030` (feat)

## Files Created/Modified
- `apps/scraper/scraper/schemas.py` - Added SyncResult dataclass
- `apps/scraper/scraper/backend_sync.py` - push/update return SyncResult, added archive_products method
- `apps/scraper/scraper/change_detection.py` - Soft-delete mark_removed, removed_at column, returning product detection
- `apps/scraper/scraper/pipeline.py` - Selective hash updates via accepted_ids, archive call for removed products

## Decisions Made
- SyncResult as dataclass in schemas.py (consistent with existing ScrapedProduct/ChangeReport pattern)
- Soft-delete via removed_at TEXT column with ALTER TABLE migration for backward compatibility
- Returning products treated as "changed" (not "new") to trigger update flow in backend
- Selective hash update filters through accepted_ids set for O(1) lookups

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Selective hash updates ensure failed products are retried automatically
- Soft-delete preserves SQLite tracking state for removed products
- Backend archive notification completes the product lifecycle loop
- Ready for next plan in Phase 17

---
*Phase: 17-scraper-hardening*
*Completed: 2026-04-19*
