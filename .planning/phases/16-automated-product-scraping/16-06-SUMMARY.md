---
phase: 16-automated-product-scraping
plan: 06
subsystem: api
tags: [asyncio, orchestrator, cli, pipeline, scraper, nightly-job]

# Dependency graph
requires:
  - phase: 16-01
    provides: SitemapService for fetching product URLs
  - phase: 16-02
    provides: ProductScraper for scraping product pages
  - phase: 16-03
    provides: ChangeDetectionService for diff tracking
  - phase: 16-04
    provides: DbSyncService for PostgreSQL sync
  - phase: 16-05
    provides: VectorSyncService for Qdrant embedding sync
provides:
  - ScraperOrchestrator service coordinating full scrape-diff-sync pipeline
  - CLI entry point (python -m scripts.run_scraper) for nightly execution
  - Dry-run mode for safe testing without syncing
  - Per-store parallel execution via asyncio.gather
  - Conditional re-clustering after pipeline completion
affects: [deployment, cron-scheduling]

# Tech tracking
tech-stack:
  added: [argparse]
  patterns: [pipeline-orchestrator, cli-entry-point, dry-run-mode, error-isolation]

key-files:
  created:
    - apps/backend/src/features/scraper/service/orchestrator.py
    - apps/backend/scripts/run_scraper.py
  modified: []

key-decisions:
  - "Services initialized per run_store call, not in __init__ — they need async setup"
  - "Per-store parallelism via asyncio.gather, sequential within store (rate limiting)"
  - "WooCommerce sync is best-effort — failures logged but not fatal"
  - "Error isolation: individual store failures caught and returned as ScrapeResult with errors"
  - "Re-clustering decision uses product count from PostgreSQL vs change threshold"
  - "CLI follows seed_bootstrap.py pattern for standalone script execution"

patterns-established:
  - "Pipeline orchestrator: init services -> sitemap -> scrape -> diff -> sync -> recluster"
  - "CLI script pattern: argparse + asyncio.run(main()) with exit codes"
  - "Dry-run support via flag propagation through orchestrator methods"

issues-created: []

# Metrics
duration: 8min
completed: 2026-03-18
---

# Phase 16 Plan 06: Orchestrator and CLI Summary

**ScraperOrchestrator coordinating full scrape-diff-sync pipeline with CLI entry point, dry-run mode, and per-store parallel execution**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-18T09:00:00Z
- **Completed:** 2026-03-18T09:08:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- ScraperOrchestrator with run_store (single-store pipeline) and run_all (multi-store parallel with re-clustering)
- Error isolation: individual store failures don't crash the pipeline
- CLI entry point with --store, --dry-run, --list-stores, --verbose flags
- Formatted summary table output showing per-store results, sync counts, recluster status, and duration
- Phase 16 complete: automated scraper replaces manual `apps/The Sprapper/` workflow

## Task Commits

Each task was committed atomically:

1. **Task 1: Create per-site scrape-and-sync pipeline orchestrator** - `5787aed` (feat)
2. **Task 2: Create CLI entry point script for nightly execution** - `ae99dfd` (feat)

**Plan metadata:** next commit (docs: complete plan)

## Files Created/Modified
- `apps/backend/src/features/scraper/service/orchestrator.py` - ScraperOrchestrator with run_store and run_all methods
- `apps/backend/scripts/run_scraper.py` - CLI entry point with argparse, summary table, exit codes

## Decisions Made
- Services initialized in run_store (not __init__) because they require async setup
- Per-store parallelism with asyncio.gather; sequential within store for rate limiting
- WooCommerce sync wrapped in try/except as best-effort (non-fatal)
- Engine created per sync operation and disposed after — avoids connection leaks
- Dry-run skips steps 5-6 (sync and hash updates) but runs sitemap, scrape, and diff normally
- Force-enable store when explicitly requested via --store flag

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Full automated scraper pipeline ready for nightly execution
- All 6 plans of Phase 16 complete: sitemap, scraper, change detection, DB sync, vector sync, orchestrator
- Ready for deployment: add cron job calling `python -m scripts.run_scraper`
- `apps/The Sprapper/` manual workflow can be retired

---
*Phase: 16-automated-product-scraping*
*Completed: 2026-03-18*
