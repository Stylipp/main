---
phase: 04-user-onboarding
plan: 02
subsystem: api
tags: [fastapi, onboarding, rocchio, qdrant, embedding, price-profile, s3]

# Dependency graph
requires:
  - phase: 03-clustering-cold-start
    provides: ColdStartService with diversity injection (3/20 ratio)
  - phase: 02-product-ingestion
    provides: Qdrant products collection, EmbeddingService, QualityGateService
  - phase: 04-01
    provides: User model with onboarding fields, auth endpoints
provides:
  - POST /api/onboarding/photos (upload + quality gate + embedding)
  - POST /api/onboarding/calibration-items (cold-start feed)
  - POST /api/onboarding/complete (user vector + price profile)
  - Qdrant user_profiles collection
  - Modified Rocchio user vector computation
  - IQR-based price profiling
affects: [feed-generation, learning, personalization]

# Tech tracking
tech-stack:
  added: [numpy]
  patterns: [modified-rocchio, iqr-price-profile, qdrant-user-profiles]

key-files:
  created:
    - apps/backend/src/features/onboarding/router/router.py
    - apps/backend/src/features/onboarding/service/service.py
    - apps/backend/src/features/onboarding/service/user_vector.py
    - apps/backend/src/features/onboarding/schemas/schemas.py
  modified:
    - apps/backend/src/main.py
    - apps/backend/src/core/qdrant.py
    - apps/backend/src/core/config.py

key-decisions:
  - "gamma=0.25 for Modified Rocchio (deviates from PROJECT.md's 0.7 per research recommendation)"
  - "Enriched CalibrationItem with product details from PostgreSQL (title, price, currency, image_url)"

patterns-established:
  - "Modified Rocchio: 0.3*photo + 1.0*liked - 0.25*disliked, L2-normalized"
  - "IQR-based price profile from liked items only (Q1-1.5*IQR to Q3+1.5*IQR)"
  - "user_profiles Qdrant collection (768-dim, cosine, on-disk payload)"

issues-created: []

# Metrics
duration: 7min
completed: 2026-03-02
---

# Phase 4 Plan 2: Onboarding Backend API Summary

**Complete onboarding API with photo upload, calibration items via cold-start service, and user vector computation using Modified Rocchio (alpha=0.3, beta=1.0, gamma=0.25) with IQR price profiling**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-02T07:27:10Z
- **Completed:** 2026-03-02T07:34:18Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Photo upload endpoint with quality validation (QualityGateService), S3 storage, and 768-dim FashionSigLIP embedding generation
- Calibration items endpoint returning 15 diverse products from ColdStartService with product details enriched from PostgreSQL
- Calibration completion endpoint computing user vector via Modified Rocchio and IQR price profile, storing vector in Qdrant and updating User in PostgreSQL
- Qdrant user_profiles collection (768-dim, cosine distance) created at startup

## Task Commits

Each task was committed atomically:

1. **Task 1: Create photo upload and calibration items endpoints** - `8718c78` (feat)
2. **Task 2: Create calibration completion endpoint with user vector and price profile** - `6ce3230` (feat)

## Files Created/Modified
- `apps/backend/src/features/onboarding/__init__.py` - Feature package init
- `apps/backend/src/features/onboarding/router/__init__.py` - Router package init
- `apps/backend/src/features/onboarding/router/router.py` - 3 endpoints: POST /photos, /calibration-items, /complete
- `apps/backend/src/features/onboarding/service/__init__.py` - Service package init
- `apps/backend/src/features/onboarding/service/service.py` - OnboardingService with upload_and_embed_photo, get_calibration_items, complete_calibration
- `apps/backend/src/features/onboarding/service/user_vector.py` - Pure functions: compute_user_vector (Modified Rocchio), initialize_price_profile (IQR)
- `apps/backend/src/features/onboarding/schemas/__init__.py` - Schemas package init
- `apps/backend/src/features/onboarding/schemas/schemas.py` - 6 Pydantic models for all request/response types
- `apps/backend/src/main.py` - Added onboarding router + ensure_user_profiles_collection() in lifespan
- `apps/backend/src/core/qdrant.py` - Added ensure_user_profiles_collection() (768-dim, cosine, on-disk payload)
- `apps/backend/src/core/config.py` - Added user_profiles_collection setting

## Decisions Made
- Used gamma=0.25 for Modified Rocchio negative signal weight instead of PROJECT.md's 0.7 — per 04-RESEARCH.md recommendation, 0.7 is too aggressive for sparse calibration data (~5-6 dislikes). Standard Rocchio literature recommends 0.15-0.25.
- Enriched CalibrationItem response with product details (title, price, currency, image_url) from PostgreSQL since ColdStartService only returns product_id/score/cluster_index/is_diversity.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Enriched calibration items with product details from PostgreSQL**
- **Found during:** Task 1 (calibration items endpoint)
- **Issue:** ColdStartService returns ColdStartMatch with product_id/score/cluster_index/is_diversity but no product details. Frontend needs title, price, currency, image_url to render calibration cards.
- **Fix:** Added PostgreSQL product lookup in get_calibration_items() to enrich each CalibrationItem with product details
- **Files modified:** apps/backend/src/features/onboarding/service/service.py
- **Verification:** CalibrationItem schema includes all required fields
- **Committed in:** 8718c78 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical), 0 deferred
**Impact on plan:** Auto-fix necessary for frontend usability. No scope creep.

## Issues Encountered
None

## Next Phase Readiness
- Onboarding backend API complete — 3 endpoints ready for frontend integration
- User vector computation and price profiling operational
- Ready for 04-03 (onboarding data model/migration if needed) or 04-04/04-05 (frontend flows)

---
*Phase: 04-user-onboarding*
*Completed: 2026-03-02*
