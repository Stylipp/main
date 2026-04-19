---
phase: 17-scraper-hardening
plan: 05
subsystem: scraper, api
tags: [json-ld, woocommerce, shopify, hebrew, unicode, normalization]

# Dependency graph
requires:
  - phase: 17-04
    provides: selective hash updates, soft-delete mark_removed
provides:
  - stable platform-native product IDs (sku, data-product_id, productGroupID)
  - prefixed external_id format ({platform}_{id} or md5_{hash})
  - Hebrew apostrophe normalization (geresh → ASCII) in category mapping
  - junk category exclusion (uncategorized, ללא קטגוריה, home, בית)
affects: [scraper, feed, ingestion]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Platform-prefixed external_id format: {platform}_{id} or md5_{hash}"
    - "Unicode NFC + apostrophe normalization before token matching"

key-files:
  created: []
  modified:
    - apps/scraper/scraper/product_scraper.py
    - apps/backend/src/features/products/utils/category.py

key-decisions:
  - "Stable ID priority: JSON-LD sku → data-product_id → productGroupID → md5 fallback"
  - "Platform prefix from StoreConfig.platform (woo, shopify, etc.)"
  - "Existing md5 IDs grandfathered — no migration, new format won't collide"
  - "All apostrophe variants (U+05F3, U+2019, U+02BC, U+2018) normalize to ASCII before token matching"

patterns-established:
  - "Stable ID extraction cascade: structured data → HTML attributes → fallback hash"

issues-created: []

# Metrics
duration: 3min
completed: 2026-04-19
---

# Phase 17 Plan 5: Stable Source IDs & Hebrew Normalization Summary

**Platform-native product ID extraction (sku/data-product_id/productGroupID) with prefixed external_id format, plus Unicode apostrophe normalization and junk category exclusion for Hebrew category mapping**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-19T20:17:46Z
- **Completed:** 2026-04-19T20:20:17Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Stable source ID extraction from JSON-LD sku, WooCommerce data-product_id, and Shopify productGroupID
- Platform-prefixed external_id format (`woo_{id}`, `shopify_{id}`, `md5_{hash}`)
- `_extract_jsonld` now returns raw JSON-LD node alongside merged data for sku access
- Hebrew geresh (׳) and smart quote variants normalized to ASCII apostrophe before category token matching
- Junk category exclusions expanded: `ללא קטגוריה`, `לא מסווג`, `בית`, `דף הבית`, `home`

## Task Commits

Each task was committed atomically:

1. **Task 1: Add stable source ID extraction** - `a9e34b7` (feat)
2. **Task 2: Hebrew apostrophe normalization** - `784d2c6` (feat)

## Files Created/Modified
- `apps/scraper/scraper/product_scraper.py` - Added `_extract_stable_id` function, updated `_extract_jsonld` to return raw node, prefixed external_id format
- `apps/backend/src/features/products/utils/category.py` - Added Unicode NFC normalization, apostrophe variant replacement, expanded junk category exclusions

## Decisions Made
- Stable ID priority: JSON-LD sku → data-product_id → productGroupID → md5 fallback
- Platform prefix from StoreConfig.platform field (already existed)
- Existing md5(url) IDs grandfathered — new format uses `md5_` prefix, won't collide with old bare hashes
- All apostrophe variants normalized to ASCII before token matching — keyword set can use single form
- Kept both geresh and ASCII forms in keyword sets (harmless redundancy, defensive)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Ready for 17-06-PLAN.md (final plan in Phase 17)
- Stable IDs will produce different external_id values for new products; existing products unaffected

---
*Phase: 17-scraper-hardening*
*Completed: 2026-04-19*
