---
phase: 02-product-ingestion-embeddings
plan: 06
subsystem: database, infra
tags: [woocommerce, qdrant, fashionsiglip, seeding, docker, alembic]

# Dependency graph
requires:
  - phase: 02-05
    provides: IngestionService pipeline (fetch → validate → embed → store)
  - phase: 02-04
    provides: WooCommerce client and ProductTransformer
provides:
  - Bootstrap seeding script fetching 478 products from WooCommerce
  - Alembic migration creating users and products tables
  - Auto-seeding entrypoint (skips if products already exist)
  - ~400+ products with FashionSigLIP embeddings in Qdrant
affects: [phase-3-clustering, phase-4-onboarding, phase-5-feed]

# Tech tracking
tech-stack:
  added: []
  patterns: [entrypoint-auto-seeding, alembic-table-creation]

key-files:
  created:
    - apps/backend/scripts/seed_bootstrap.py
    - apps/backend/scripts/__init__.py
    - apps/backend/data/bootstrap_products.json
    - apps/backend/alembic/versions/2026_02_18_0001-a1b2c3d4e5f6_create_users_and_products_tables.py
  modified:
    - apps/backend/entrypoint.sh
    - apps/backend/Dockerfile
    - infra/docker-compose.yml
    - .github/workflows/ci.yml

key-decisions:
  - "Used real WooCommerce store instead of Unsplash placeholder images"
  - "Auto-seed in entrypoint.sh with product count check to skip if already seeded"
  - "Created Alembic migration for users + products tables (was missing)"

patterns-established:
  - "Entrypoint auto-seeding: check product count, seed if empty, then start server"

issues-created: []

# Metrics
duration: ~15min
completed: 2026-02-18
---

# Phase 2 Plan 6: Bootstrap Store Seeding Summary

**WooCommerce-based seeding script ingesting ~400+ real fashion products with FashionSigLIP embeddings via auto-seeding Docker entrypoint**

## Performance

- **Duration:** ~15 min (including debugging missing migration)
- **Started:** 2026-02-18T17:00:00Z
- **Completed:** 2026-02-18T17:15:35Z
- **Tasks:** 2 (1 auto + 1 checkpoint)
- **Files modified:** 8

## Accomplishments
- Bootstrap seeding script that fetches all published products from WooCommerce store (478 products)
- ~400+ products successfully ingested with FashionSigLIP embeddings stored in Qdrant
- Auto-seeding logic in entrypoint.sh — checks product count, seeds only if database is empty
- Alembic migration creating users and products tables (was missing from prior phases)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create bootstrap seeding script** - `6bc38d3` (feat)
2. **WooCommerce env vars in CI/Docker** - `d32fbe4` (chore, user commit)
3. **Dockerfile system deps + scripts copy** - `5646f7a` (chore, user commit)
4. **Entrypoint auto-seeding fix** - `cdce51d` (fix)
5. **Alembic migration for tables** - `0d9fff5` (feat)

## Files Created/Modified
- `apps/backend/scripts/seed_bootstrap.py` - WooCommerce seeding script with full ingestion pipeline
- `apps/backend/scripts/__init__.py` - Package init for scripts module
- `apps/backend/data/bootstrap_products.json` - Placeholder JSON (script generates from WooCommerce API)
- `apps/backend/alembic/versions/2026_02_18_0001-a1b2c3d4e5f6_create_users_and_products_tables.py` - Migration creating users + products tables
- `apps/backend/entrypoint.sh` - Added auto-seeding with product count check
- `apps/backend/Dockerfile` - Added libgl1/libglib2.0/libxcb1 deps, copy scripts/data dirs
- `infra/docker-compose.yml` - Added WooCommerce env vars
- `.github/workflows/ci.yml` - Added WooCommerce secrets to CI build

## Decisions Made
- Used real WooCommerce store (woo-cloudways) instead of Unsplash placeholder images — provides realistic product data for development
- Added auto-seeding to entrypoint.sh with idempotent check (counts products, skips if >0)
- Created Alembic migration for both users and products tables — was missing from Phase 1

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Used WooCommerce API instead of Unsplash**
- **Found during:** Task 1 (Seeding script creation)
- **Issue:** Plan specified Unsplash images but real WooCommerce store exists with 478 products
- **Fix:** Script fetches from WooCommerce API using existing client from 02-04
- **Verification:** 478 products fetched, ~400+ ingested successfully

**2. [Rule 3 - Blocking] Created missing Alembic migration**
- **Found during:** Checkpoint verification (seeding failed with "relation products does not exist")
- **Issue:** No Alembic migration existed to create users/products tables despite models existing
- **Fix:** Created migration `a1b2c3d4e5f6` with both tables and all indexes
- **Verification:** `alembic upgrade head` runs successfully, seeding completes

**3. [Rule 2 - Missing Critical] Added auto-seeding to entrypoint.sh**
- **Found during:** User request during checkpoint
- **Issue:** Manual seeding required running separate Docker command
- **Fix:** Added product count check + automatic seeding to entrypoint.sh
- **Verification:** Container starts, detects empty DB, seeds, then starts uvicorn

---

**Total deviations:** 3 auto-fixed (1 bug, 1 blocking, 1 missing critical), 0 deferred
**Impact on plan:** All fixes necessary for functional seeding. WooCommerce data is better than placeholder.

## Issues Encountered
- Qdrant client version mismatch warning (1.16.2 client vs 1.7.4 server) — functional but should pin compatible version later
- ~16% of products failed quality gate (expected — some store images don't meet quality thresholds)

## Next Phase Readiness
- Phase 2 complete: Full product ingestion pipeline operational
- ~400+ products with embeddings in Qdrant ready for clustering
- Ready for Phase 3 (Clustering & Cold Start System)

---
*Phase: 02-product-ingestion-embeddings*
*Completed: 2026-02-18*
