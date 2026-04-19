---
phase: 17-scraper-hardening
plan: 01
subsystem: api
tags: [pydantic, fastapi, http-207, batch-ingest]

# Dependency graph
requires:
  - phase: 16-scraper-sync
    provides: batch ingest endpoint and scraper pipeline
provides:
  - Per-product accepted_ids and rejected arrays in BatchIngestResponse
  - HTTP 207 partial success status for mixed results
  - RejectedItem schema with retryable flag
affects: [17-02 selective hash updates, 17-03 retry on failure]

# Tech tracking
tech-stack:
  added: []
  patterns: [HTTP 207 Multi-Status for partial batch results]

key-files:
  created: []
  modified:
    - apps/backend/src/features/products/schemas/schemas.py
    - apps/backend/src/features/products/router/router.py

key-decisions:
  - "Transient exceptions retryable=True, validation/quality failures retryable=False"
  - "HTTP 207 only when BOTH accepted and rejected exist (partial success)"

patterns-established:
  - "RejectedItem schema: structured error reporting with retryable flag"

issues-created: []

# Metrics
duration: 3min
completed: 2026-04-19
---

# Phase 17 Plan 01: Per-Product Sync Contract Summary

**RejectedItem schema + accepted_ids/rejected arrays in BatchIngestResponse, HTTP 207 on partial success**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-19T14:35:06Z
- **Completed:** 2026-04-19T14:37:45Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added RejectedItem Pydantic model with external_id, store_id, error, retryable fields
- Replaced generic errors list[dict] with typed accepted_ids and rejected arrays
- Router returns HTTP 207 Multi-Status on partial success, 200 on full success
- Transient errors marked retryable=True, validation failures retryable=False

## Task Commits

Each task was committed atomically:

1. **Task 1: Add RejectedItem schema and update BatchIngestResponse** - `e2be469` (feat — committed in prior session as part of 06-05)
2. **Task 2: Update ingest_batch router for per-item tracking and HTTP 207** - `52ffad1` (feat)

## Files Created/Modified
- `apps/backend/src/features/products/schemas/schemas.py` - Added RejectedItem model, updated BatchIngestResponse fields
- `apps/backend/src/features/products/router/router.py` - Per-item tracking with accepted_ids/rejected, HTTP 207 logic

## Decisions Made
- Transient exceptions (unexpected errors) marked retryable=True; validation/quality gate failures marked retryable=False — scraper can distinguish permanent vs transient failures
- HTTP 207 only when both accepted and rejected items exist — pure success stays 200, pure failure stays 200 with failed count (scraper checks the arrays, not just status code)

## Deviations from Plan

None - plan executed exactly as written.

Note: Task 1 schema changes were already committed in a prior session (e2be469) alongside 06-05 feed work. No additional commit needed for Task 1.

## Issues Encountered
None

## Next Phase Readiness
- Per-product sync contract ready for scraper integration
- Next plan (17-02) can consume accepted_ids to selectively update hashes
- rejected array with retryable flag enables retry logic in 17-03

---
*Phase: 17-scraper-hardening*
*Completed: 2026-04-19*
