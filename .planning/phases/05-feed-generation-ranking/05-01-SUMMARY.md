---
phase: 05-feed-generation-ranking
plan: 01
subsystem: feed
tags: [scoring, ranking, tdd, math, freshness-decay, price-affinity, normalization]

# Dependency graph
requires:
  - phase: 03-clustering-cold-start
    provides: cluster priors, K-means style clusters
  - phase: 04-user-onboarding
    provides: user price profile (median, std), user vectors
provides:
  - compute_freshness_score (14-day half-life exponential decay)
  - compute_price_affinity (log-normal Gaussian)
  - normalize_scores (min-max to [0,1])
  - rank_candidates (multi-factor weighted scoring pipeline)
  - RankedCandidate dataclass
affects: [feed-service, feed-api, diversity-injection]

# Tech tracking
tech-stack:
  added: []
  patterns: [pure-function scoring, per-batch normalization, weighted multi-factor ranking]

key-files:
  created:
    - apps/backend/src/features/feed/utils/scoring.py
    - apps/backend/src/features/feed/service/ranking_service.py
    - apps/backend/tests/features/feed/test_scoring.py
  modified: []

key-decisions:
  - "Missing cluster prior defaults to 0.0 (not 0.5) — unknown clusters get no prior affinity"
  - "ISO string created_at parsed via datetime.fromisoformat() with naive-timezone fallback to UTC"
  - "Pure stdlib math only — no numpy dependency for scoring functions"
  - "log_sigma floor of 0.1 prevents division-by-zero in price affinity"

patterns-established:
  - "Pure scoring functions in utils/scoring.py, orchestration in service/ranking_service.py"
  - "Per-batch min-max normalization before applying weights to prevent cosine domination"

issues-created: []

# Metrics
duration: 6min
completed: 2026-03-17
---

# Phase 5 Plan 1: Scoring & Ranking Functions (TDD) Summary

**Multi-factor scoring pipeline with 14-day freshness decay, log-normal price affinity, min-max normalization, and 0.65/0.15/0.10/0.10 weighted ranking — 37 tests covering all edge cases**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-17T17:57:49Z
- **Completed:** 2026-03-17T18:04:03Z
- **Tasks:** RED + GREEN (TDD cycle)
- **Files created:** 7

## Accomplishments
- 4 pure scoring functions: freshness decay, price affinity, score normalization, candidate ranking
- RankedCandidate dataclass with full component score transparency
- 37 comprehensive tests across 5 test classes covering edge cases (zero/negative prices, future dates, uniform scores, empty input, single element, log-space symmetry)
- Per-batch normalization prevents cosine similarity from dominating the ranking

## TDD Phases

### RED
Wrote 37 failing tests in 5 classes:
- `TestComputeFreshnessScore` (8 tests): decay at 0/14/28/365 days, future clamp, monotonic decrease
- `TestComputePriceAffinity` (11 tests): median match, log-space symmetry, zero/negative fallbacks, bounds check
- `TestNormalizeScores` (9 tests): basic/uniform/empty/single/negative/near-uniform
- `TestRankedCandidate` (1 test): dataclass fields
- `TestRankCandidates` (8 tests): empty/single/three-candidate ordering, weight sum, component population

Tests failed with `ModuleNotFoundError` as expected.

### GREEN
Implemented:
- `scoring.py`: `compute_freshness_score` (exp(-lambda * days), lambda=ln(2)/14), `compute_price_affinity` (log-normal Gaussian with sigma floor), `normalize_scores` (min-max with uniform/empty/single guards)
- `ranking_service.py`: `RankedCandidate` dataclass, `rank_candidates` (extract raw -> normalize per-batch -> apply weights 0.65/0.15/0.10/0.10 -> sort descending)

All 37 tests pass.

### REFACTOR
Not needed — code is already minimal and follows project patterns.

## Task Commits

1. **RED: Failing tests** - `6c48bd0` (test)
2. **GREEN: Implementation** - `c7a354f` (feat)

## Files Created/Modified
- `apps/backend/src/features/feed/__init__.py` - Package init
- `apps/backend/src/features/feed/utils/__init__.py` - Package init
- `apps/backend/src/features/feed/utils/scoring.py` - Pure scoring functions (freshness, price affinity, normalization)
- `apps/backend/src/features/feed/service/__init__.py` - Package init
- `apps/backend/src/features/feed/service/ranking_service.py` - RankedCandidate dataclass + rank_candidates orchestrator
- `apps/backend/tests/features/feed/__init__.py` - Package init
- `apps/backend/tests/features/feed/test_scoring.py` - 37 tests across 5 classes

## Decisions Made
- Missing cluster prior defaults to 0.0 (not 0.5) — treats unknown clusters as having no prior affinity rather than neutral
- ISO string `created_at` parsing handled via `datetime.fromisoformat()` with naive-timezone fallback to UTC
- No numpy dependency — pure stdlib `math` sufficient for these calculations
- `log_sigma` floor of 0.1 to prevent division-by-zero edge case in price affinity

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness
- Scoring functions ready for feed service integration in 05-02-PLAN.md
- `rank_candidates` accepts Qdrant ScoredPoint-like objects — ready for real query results
- All edge cases covered — empty candidates, missing priors, zero prices handled gracefully

---
*Phase: 05-feed-generation-ranking*
*Completed: 2026-03-17*
