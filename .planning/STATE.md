# Project State

## Project Reference

See: [.planning/PROJECT.md](.planning/PROJECT.md) (updated 2026-01-27)

**Core value:** Users get relevant fashion recommendations immediately—no lengthy questionnaires, no 50-swipe training period, no guessing what to search for.

**Current focus:** Phase 4 in progress — User Onboarding & Profiles (4/5 plans complete)

## Current Position

Phase: 4 of 15 (User Onboarding & Profiles)
Plan: 4 of 5 in current phase
Status: In progress
Last activity: 2026-03-02 — Completed 04-04-PLAN.md

Progress: █████████████░░ Phase 1 ✓ | Phase 2 ✓ | Phase 3 ✓ | Phase 4: 4/5

## Performance Metrics

**Velocity:**
- Total plans completed: 22
- Average duration: ~9 min
- Total execution time: ~3h 22m

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 9/9 ✓ | ~1h 34m | ~10m |
| 2 | 6/6 ✓ | ~1h 6m | ~11m |
| 3 | 3/3 ✓ | 14m | ~5m |
| 4 | 4/5 | 27m | ~7m |

**Recent Trend:**
- Last 5 plans: 03-03, 04-01, 04-02, 04-03, 04-04
- Trend: Steady/accelerating

## Accumulated Context

### Decisions

| Phase | Decision | Rationale |
|-------|----------|-----------|
| 01-04 | Alembic manages all DB schema (no init.sql) | Consistent with 01-03 Alembic setup, single source of truth for schema |
| 01-04 | PostgreSQL 16, Qdrant v1.7.4, Redis 7 Alpine | Pinned versions for reproducibility |
| 01-04 | Named Docker volumes for persistence | Data survives container restarts |
| 01-05 | ES256 (ECDSA P-256) for JWT signing | Smaller keys, faster verification than RSA |
| 01-05 | Volume-mounted PEM files for key storage | Better security than env variables |
| 01-05 | Feature folder convention: features/auth/{router,service,schemas,utils}/ | Consistent codebase structure |
| 01-06 | aioboto3 for true async S3 operations | Non-blocking S3 client for FastAPI |
| 01-06 | Key pattern: user_photos/{user_id}/{uuid}.jpg | Organized storage structure |
| 02-01 | Qdrant 768-dim vectors with cosine similarity | FashionSigLIP embedding dimension |
| 02-01 | Async Qdrant client singleton | Connection reuse across requests |
| 02-03 | Module-level QualityGateService singleton | Stateless service, safe to reuse across requests |
| 02-03 | opencv-python-headless over opencv-python | No GUI dependencies needed in backend |
| 02-05 | Router prefix="/products" with /api in main.py | Matches existing auth, ai, storage router convention |
| 02-05 | IngestionResult.quality_issues uses default_factory=list | Cleaner API, avoids None checks |
| 02-06 | Real WooCommerce store instead of Unsplash placeholders | Realistic product data for development |
| 02-06 | Auto-seed in entrypoint.sh with product count check | Idempotent seeding on container start |
| 02-06 | Alembic migration for users + products tables | Was missing from Phase 1, required for seeding |
| 03-01 | Centroid vectors in Qdrant only (not duplicated in PG) | Follows Phase 2 pattern — Qdrant is source of truth for vectors |
| 03-01 | Full replacement upsert for cluster rebuild | Delete all + insert new ensures rebuild consistency |
| 03-01 | asyncio.to_thread for CPU-intensive sklearn ops | Prevents event loop blocking during K-means/silhouette |
| 03-01 | Silhouette analysis for optimal k determination | Better cluster quality vs fixed k |
| 03-02 | Hardcoded 3/20 diversity injection (not configurable) | Per PROJECT.md, prevents echo chambers |
| 03-02 | Proportional product allocation by similarity score | Higher-similarity clusters get more items |
| 03-02 | Diversity clusters = 4th-5th ranked by similarity | Adjacent clusters, not random |
| 03-03 | No auto-clustering in lifespan (API/entrypoint only) | CPU-intensive, would block startup |
| 03-03 | 768-dim embedding validation on cold-start endpoint | Clear error messages for invalid input |
| 04-01 | Task execution order reversed (Task 2 before Task 1) | Avoid broken intermediate state — model fields needed before schema references |
| 04-01 | Service raises ValueError, router converts to HTTPException | Clean separation of concerns |
| 04-01 | GET /auth/me queries DB for full User record | Frontend needs onboarding_completed status, not just JWT payload |
| 04-02 | gamma=0.25 for Modified Rocchio (not PROJECT.md's 0.7) | Too aggressive for sparse calibration data (~5-6 dislikes); standard range 0.15-0.25 |
| 04-02 | Enriched CalibrationItem with product details from PostgreSQL | ColdStartService only returns IDs; frontend needs title, price, image_url |
| 04-03 | Lazy accessor pattern for auth store in API client | verbatimModuleSyntax prohibits CommonJS require(); setAuthStoreAccessor() avoids circular dep |
| 04-03 | Zod v4 with @hookform/resolvers@5 | Current latest, native support, different API from v3 |
| 04-03 | 401 interceptor only clears auth when token present | Prevents interference with login/register error handling |
| 04-04 | React 19 "adjust state during render" pattern for direction tracking | refs-during-render and setState-in-effects prohibited by React 19 strict ESLint |
| 04-04 | Direct progress reads from hooks instead of effect-based sync | Avoids react-hooks/set-state-in-effect violations |

### Deferred Issues

None yet.

### Pending Todos

None yet.

### Blockers/Concerns

- ~~uuid-ossp extension not yet created~~ — Resolved in 02-01 migration
- ~~Docker PostgreSQL connection from Windows requires manual verification~~ — Verified working in 02-06
- Qdrant client version mismatch (1.16.2 vs server 1.7.4) — functional but should pin compatible version

## Session Continuity

Last session: 2026-03-02
Stopped at: Completed 04-04-PLAN.md (Onboarding Layout & Photo Upload: MobileStepper, AnimatePresence transitions, photo upload with compression)
Resume file: None
