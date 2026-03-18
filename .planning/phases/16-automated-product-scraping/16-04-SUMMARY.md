---
phase: 16-automated-product-scraping
plan: 04
subsystem: api, database
tags: [woocommerce, sqlalchemy, httpx, postgresql, batch-operations]

# Dependency graph
requires:
  - phase: 16-01
    provides: ScrapedProduct schema, scraper feature structure
  - phase: 02-06
    provides: WooCommerceClient, ProductRepository, Product model
provides:
  - WooCommerceClient batch_create_products and batch_update_products (chunked at 100)
  - WooCommerceClient find_product_by_sku for SKU-based lookups
  - ProductRepository.update method keyed on (external_id, store_id)
  - DbSyncService with sync_new_products, sync_changed_products, remove_products
affects: [16-05, 16-06]

# Tech tracking
tech-stack:
  added: []
  patterns: [batch-chunking-at-100, log-but-retain-removed-products, woocommerce-secondary-to-postgresql]

key-files:
  created:
    - apps/backend/src/features/scraper/service/db_sync_service.py
  modified:
    - apps/backend/src/features/products/service/woocommerce_client.py
    - apps/backend/src/features/products/service/product_repository.py

key-decisions:
  - "WooCommerce errors are logged but never crash the pipeline (WooCommerce is secondary)"
  - "Products removed from sitemap are logged but retained in PostgreSQL to preserve user interaction history"
  - "Products without images are skipped during sync (embeddings require images)"

patterns-established:
  - "Batch chunking at 100 items: WooCommerce REST API v3 limit for batch operations"
  - "Graceful degradation: WooCommerce sync failures produce warnings, not exceptions"

issues-created: []

# Metrics
duration: 5min
completed: 2026-03-18
---

# Plan 16-04: WooCommerce Batch & DB Sync Summary

**WooCommerceClient extended with batch create/update/SKU-lookup and DbSyncService created for PostgreSQL product upserts with graceful error handling**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-18
- **Completed:** 2026-03-18
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Extended WooCommerceClient with batch_create_products, batch_update_products (both chunked at 100), and find_product_by_sku
- Added ProductRepository.update method keyed on (external_id, store_id) composite key
- Created DbSyncService with sync_new_products, sync_changed_products, and remove_products coordinating PostgreSQL upserts
- All WooCommerce errors logged but never crash the pipeline (graceful degradation)
- Removed products logged as warnings but retained in database to preserve user interaction history

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend WooCommerceClient with batch create and update operations** - `88d2d55` (feat)
2. **Task 2: Create database sync service for PostgreSQL product upserts** - `db2caa6` (feat)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified
- `apps/backend/src/features/products/service/woocommerce_client.py` - Added batch_create_products, batch_update_products (100-item chunks), find_product_by_sku with full error handling
- `apps/backend/src/features/products/service/product_repository.py` - Added update() method for field-level updates by (external_id, store_id)
- `apps/backend/src/features/scraper/service/db_sync_service.py` - New service coordinating ScrapedProduct-to-PostgreSQL sync for new, changed, and removed products

## Decisions Made
- WooCommerce errors (HTTP status errors, timeouts) are caught and logged but never propagate — WooCommerce is secondary to PostgreSQL+Qdrant
- Removed products are logged but not deleted from PostgreSQL to preserve user interactions (swipes, saves, collections)
- Products without image_urls are skipped during sync since embeddings cannot be generated without images
- Batch operations use the WooCommerce REST API v3 `/products/batch` endpoint with 100-item chunking

## Deviations from Plan

None - plan executed exactly as written

## Issues Encountered
None

## Next Phase Readiness
- WooCommerce batch sync layer ready for the orchestration pipeline (Plan 16-05/16-06)
- DbSyncService can be composed with WooCommerceClient for full new/changed/removed product handling
- ProductRepository.update enables field-level updates without full replacement

---
*Phase: 16-automated-product-scraping*
*Completed: 2026-03-18*
