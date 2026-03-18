---
phase: 16-automated-product-scraping
plan: 02
subsystem: api
tags: [httpx, beautifulsoup, xml, json-ld, scraping, async]

# Dependency graph
requires:
  - phase: 16-01
    provides: Scraper feature module structure, StoreConfig, StoreSelectors, ScrapedProduct schema
provides:
  - SitemapService for async sitemap fetching and product URL extraction
  - ProductScraper for async product page scraping with JSON-LD + HTML fallback
affects: [16-03, 16-04, 16-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Async HTTP fetching with httpx.AsyncClient
    - JSON-LD product extraction with Yoast @graph support
    - HTML fallback extraction with configurable CSS selectors
    - Rate-limited batch scraping via asyncio.sleep

key-files:
  created:
    - apps/backend/src/features/scraper/service/sitemap_service.py
    - apps/backend/src/features/scraper/service/product_scraper.py
  modified: []

key-decisions:
  - "Graceful error handling: individual failures return None/empty list, never crash pipeline"
  - "XML namespace handled with both namespaced and non-namespaced fallback for maximum compatibility"
  - "JSON-LD extraction tried first (richer data), HTML selectors as fallback"
  - "Price parsing handles multiple formats: ILS, USD, EUR, European comma notation"

patterns-established:
  - "Scraper error isolation: catch-log-return pattern for individual URL failures"
  - "Sitemap index recursion: auto-detect sitemapindex and fetch sub-sitemaps"
  - "Batch scraping with progress logging every 50 items"

issues-created: []

# Metrics
duration: 8min
completed: 2026-03-18
---

# Phase 16-02: Sitemap & Product Scraper Summary

**Async sitemap fetcher and product page scraper with JSON-LD extraction ported from The Sprapper to httpx**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-18
- **Completed:** 2026-03-18
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- SitemapService that fetches XML sitemaps, handles sitemap index recursion, filters product URLs by configurable pattern, and handles XML namespaces
- ProductScraper that extracts product data via JSON-LD (with Yoast @graph support) and falls back to store-specific CSS selectors
- Rate-limited batch scraping with progress logging and graceful error handling per URL

## Task Commits

Each task was committed atomically:

1. **Task 1: Create async sitemap fetcher and URL extractor** - `a12d073` (feat)
2. **Task 2: Create async product page scraper with JSON-LD + HTML fallback extraction** - `be20c78` (feat)

**Plan metadata:** this commit (docs: complete sitemap and product scraper plan)

## Files Created/Modified
- `apps/backend/src/features/scraper/service/sitemap_service.py` - Async XML sitemap fetcher with namespace handling and sitemap index recursion
- `apps/backend/src/features/scraper/service/product_scraper.py` - Product page scraper with JSON-LD and HTML CSS selector extraction

## Decisions Made
- Graceful error handling throughout: HTTP errors, parse errors, and timeouts log warnings and return None/empty instead of raising
- XML namespace fallback: tries standard `{http://www.sitemaps.org/schemas/sitemap/0.9}` namespace first, then non-namespaced for compatibility
- JSON-LD extraction attempted before HTML selectors since it provides richer structured data
- Price parsing handles ILS/USD/EUR symbols and European comma-decimal notation
- Image extraction from JSON-LD supports string, list, and dict (with url/contentUrl/@id) formats

## Deviations from Plan

None - plan executed exactly as written

## Issues Encountered
None

## Next Phase Readiness
- SitemapService and ProductScraper ready for integration into the scraping pipeline orchestrator
- Change detection (16-03) can use ScrapedProduct objects from ProductScraper
- WooCommerce sync (16-04) can consume scraped data for upstream catalog updates

---
*Phase: 16-automated-product-scraping*
*Completed: 2026-03-18*
