---
phase: 05-feed-generation-ranking
plan: 02
subsystem: feed
tags: [feed-service, candidate-retrieval, ranking, diversity-injection, qdrant-search, shortfall-handling]

# Dependency graph
requires:
  - phase: 05-feed-generation-ranking
    plan: 01
    provides: scoring functions (freshness, price affinity, normalization), rank_candidates, RankedCandidate
  - phase: 04-user-onboarding
    provides: user vectors in Qdrant user_profiles, price profiles in PostgreSQL
  - phase: 03-clustering-cold-start
    provides: style_clusters collection with cluster priors, products with cluster_id
provides:
  - FeedService class with generate_feed() method
  - Candidate retrieval with shortfall handling
  - Diversity injection (3/20 from adjacent clusters)
affects: [feed-router, feed-api]

# Tech tracking
tech-stack:
  added: []
  patterns: [two-stage retrieval+ranking, progressive shortfall widening, diversity interleaving]

key-files:
  created:
    - apps/backend/src/features/feed/service/feed_service.py
  modified: []

key-decisions:
  - "Uses qdrant_client.search() directly (not query_points()) for v1.7.4 compatibility"
  - "No caching of cluster priors — deferred to Phase 12"
  - "Diversity clusters are 4th-5th ranked by cosine similarity (adjacent, not random)"
  - "3/20 diversity injection hardcoded per PROJECT.md"
  - "Shortfall handling: drop price filter first, then allow revisits"

patterns-established:
  - "FeedService follows same constructor pattern as ColdStartService (qdrant_client + settings)"
  - "Progressive filter widening for small-catalog robustness"
  - "Diversity interleaving reuses same chunk-based pattern as cold_start_service"

issues-created: []

# Metrics
duration: 6min
completed: 2026-03-17
---

# Phase 5 Plan 2: Feed Service - Retrieval, Ranking & Diversity Summary

**FeedService orchestrating two-stage pipeline: Qdrant candidate retrieval with progressive shortfall handling, multi-factor ranking, and mandatory 3/20 diversity injection from adjacent clusters**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-17T18:07:02Z
- **Completed:** 2026-03-17T18:14:26Z
- **Tasks:** 2
- **Files modified:** 1

## Task Commits

Each task was committed atomically:

1. **Task 1: Create FeedService with candidate retrieval and ranking** - `67fcf24` (feat)
2. **Task 2: Add diversity injection to feed generation** - `87562d3` (feat)

**Plan metadata:** `bf2b72f` (docs: complete plan)

## Accomplishments

- FeedService class with `generate_feed()` orchestrating the complete feed pipeline
- User vector loaded from Qdrant user_profiles collection (same pattern as onboarding stores it)
- Price profile loaded from PostgreSQL users.price_profile JSONB
- Cluster priors loaded from Qdrant style_clusters via scroll (no caching, deferred to Phase 12)
- Candidate retrieval via `qdrant_client.search()` with ~100 overretrieve limit and score_threshold=0.2
- Progressive shortfall handling (Pattern 4): full filters -> drop price -> allow revisits
- Diversity injection: identify 4th-5th clusters by user vector similarity, retrieve and rank diversity candidates, interleave 3 items across 20
- All 41 existing tests continue to pass

## Files Created/Modified

- `apps/backend/src/features/feed/service/feed_service.py` — FeedService class with generate_feed(), candidate retrieval, shortfall handling, diversity injection, and interleaving

## Decisions Made

- Uses `qdrant_client.search()` directly rather than the compatibility wrapper from cold_start_service — the search() method works on v1.7.4 and the wrapper is not needed here
- No caching of cluster priors (deferred to Phase 12 per RESEARCH.md Pitfall 5)
- Diversity clusters = 4th-5th ranked by cosine similarity to user vector (adjacent, not random, per Phase 03-02)
- Hardcoded 3/20 diversity count (not configurable, per PROJECT.md)
- Price filter uses generous range (0.5x min to 2.0x max) per RESEARCH.md to avoid over-filtering

## Issues Encountered

None

## Next Phase Readiness

- FeedService ready for router integration in 05-03
- generate_feed() method fully implements two-stage pipeline
- No blockers or concerns

---
*Phase: 05-feed-generation-ranking*
*Completed: 2026-03-17*
