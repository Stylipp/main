# Stylipp Brain - Tasks and Test Plan

> Source of truth: [THE_BRAIN.md](../THE_BRAIN.md)
> Purpose: track everything still needed to complete the recommendation "brain", plus the checks you can run to confirm each slice actually works.

---

## Status Legend

- `[x]` built and merged
- `[-]` partially built or built in code but still needs migration/data/application wiring
- `[ ]` not built yet

---

## Current State

### Already Built

- `[x]` Profile-state foundation on `User`
- `[x]` `profile_confidence` helper and maturity math
- `[x]` Onboarding initializes profile-state metadata
- `[x]` Feedback increments interaction counters and recalculates confidence
- `[x]` Scraper pushes scraped products directly to backend batch ingest API
- `[x]` Scraper change-detection state exists locally
- `[x]` Canonical product category mapping
- `[x]` Product category stored in PostgreSQL and Qdrant payloads
- `[x]` Feed API supports category-scoped retrieval
- `[x]` Feed UI exposes category chips and card category badge
- `[x]` Tests for profile-state helper, category mapping, and category filter wiring

### Built But Still Needs Environment Work

- `[-]` Run Alembic migrations for profile-state and product categories
- `[-]` Reingest or resync catalog so existing products get category payloads
- `[-]` Production schema is at head, but live category coverage is still weak
- `[-]` Live DB still contains historical products outside the current store catalog

### Biggest Missing Pieces

- `[ ]` Scraper-to-backend hardening for categories, sync correctness, and removals
- `[ ]` Real learning loop: swipes update the actual user vector
- `[-]` Feed modes: `trending`, `hybrid`, `personalized` are built in code and tested locally, but still need push/deploy and manual verification
- `[ ]` Auto cold-start from interactions without photo upload
- `[ ]` Exposure logging
- `[ ]` Richer feedback signals
- `[ ]` Rolling price learning
- `[ ]` Replace `cluster_prior` with popularity
- `[ ]` Multi-interest vectors

---

## Task Order

### 0. Environment and Data Prerequisites

- `[ ]` Apply the new Alembic migrations in `apps/backend`
- `[ ]` Verify `users` table has profile-state columns
- `[ ]` Verify `products` table has `category` and `raw_categories`
- `[ ]` Reingest or resync catalog data so old products get category metadata
- `[ ]` Verify Qdrant `products` payload includes `category`
- `[ ]` Measure live catalog coverage: total products, empty `raw_categories`, and category distribution
- `[ ]` Separate current-store products from stale historical products in production

### 0A. Scraper-to-Backend Hardening

- `[x]` Make scraper send `raw_categories` to backend batch ingest
- `[x]` Decide whether scraper should also send canonical `category`, or whether backend remains source of truth
- `[x]` Merge JSON-LD data with HTML category extraction instead of dropping HTML categories when JSON-LD exists
- `[x]` Preserve categories for pages where JSON-LD has title and price but breadcrumbs carry taxonomy
- `[-]` Expand category normalization to support Hebrew/store-specific labels and common junk values like `uncategorized`
- `[-]` Add category mapping tests for Hebrew labels and store-specific category names
- `[ ]` Change scraper sync result contract to include successful ids and failed ids, not only counts
- `[ ]` Update local scraper hashes only for products that were actually accepted by backend
- `[ ]` Ensure per-product backend failures are retried on the next scraper run
- `[ ]` Add backend-side product archival or soft-delete flow for removed products
- `[ ]` Exclude archived/removed products from feed retrieval and ranking
- `[ ]` Decide how archived products should be handled in Qdrant payloads or deletion
- `[ ]` Add end-to-end resync/backfill command for direct-to-backend scraper mode
- `[ ]` Replace `external_id=md5(url)` with a stable source product id when the page exposes one
- `[ ]` Add fallback strategy when stable source id is unavailable
- `[ ]` Suppress noisy merchandising/navigation labels like `new collection`, `shop`, `עמוד הבית`, and `חנות` before canonical category matching
- `[ ]` Add regression tests for 200/207 ingest responses, selective hash updates, removed/relisted products, and stable ID extraction
- `[ ]` Add a one-off production reconciliation/backfill script for legacy md5-era products and stale historical catalog rows

### 1. Complete Phase A Learning Loop

- `[ ]` Add profile update service dedicated to recommendation-state updates
- `[ ]` Move vector updates out of request path into a background task boundary
- `[ ]` Define update input contract: user id, product id, action, timestamp, profile version
- `[ ]` Implement ordered profile updates using `profile_version`
- `[ ]` Implement incremental vector update on `like`
- `[ ]` Implement incremental vector update on `dislike`
- `[ ]` Decide and implement behavior for `save`
- `[ ]` Persist updated vector back to Qdrant `user_profiles`
- `[ ]` Update `last_profile_update_at` whenever vector changes
- `[ ]` Update `profile_source` when first learned from post-onboarding behavior
- `[ ]` Add drift guardrail: cap per-update movement
- `[ ]` Add burst guardrail: dampen repeated dislikes
- `[ ]` Add stale-interest decay rule for later compatibility
- `[ ]` Add periodic full rebuild command/job for profile reconciliation

### 2. Complete Phase A Price Learning

- `[ ]` Replace onboarding-only price profile with rolling update logic
- `[ ]` Update price profile on `like`
- `[ ]` Decide whether `save` should affect price profile
- `[ ]` Keep safe defaults for users with sparse history
- `[ ]` Confirm feed ranking still behaves well when price data is weak

### 3. Complete Phase B Feed Modes

- `[-]` Add explicit feed mode enum/contract in backend
- `[-]` Add `feed_mode` to `FeedResponse`
- `[-]` Implement `trending` feed path for users without a vector
- `[-]` Implement `hybrid` feed path for weak profiles
- `[-]` Keep current vector-based path as `personalized`
- `[-]` Store mode thresholds in config instead of hardcoding
- `[-]` Apply category filtering consistently in all 3 modes
- `[-]` Add low-rate discovery injection rule to personalized mode
- `[-]` Return mode to frontend so UI can react

### 4. Complete Phase B Zero-Friction Start

- `[ ]` Remove hard dependency on onboarding-complete vector for first feed access
- `[ ]` Implement trending ranking based on interaction-derived popularity
- `[ ]` Add fallback to newest items when engagement data is too sparse
- `[ ]` Auto-create first vector after enough interactions
- `[ ]` Set `profile_source="auto_coldstart"` when that happens
- `[ ]` Add optional photo-boost flow on top of existing vector

### 5. Complete Exposure Logging

- `[ ]` Add `ExposureLog` model and migration
- `[ ]` Add backend endpoint for batched exposure events
- `[ ]` Store `session_id`, `feed_mode`, `position`, `shown_at`, `action`, `action_at`, `dwell_ms`
- `[ ]` Decide whether exposure writes are sync or buffered
- `[ ]` Wire feed frontend to emit exposure events when card becomes visible
- `[ ]` Wire swipe/save actions to complete the exposure row
- `[ ]` Protect against duplicate exposure events for the same visible card

### 6. Complete Richer Feedback Signals

- `[ ]` Add support for `opened_product`
- `[ ]` Add support for `dwell_ms`
- `[ ]` Add support for `undo` as a first-class learning signal
- `[ ]` Decide how `save` differs from `like` in vector updates
- `[ ]` Add signal-weight mapping in one shared place
- `[ ]` Make the feedback/update pipeline consume signal weights

### 7. Complete Phase D Ranking Simplification

- `[ ]` Add popularity scoring function based on real interactions
- `[ ]` Add time decay for popularity
- `[ ]` Add Bayesian smoothing / prior
- `[ ]` Replace `cluster_prior` in ranking formula with popularity
- `[ ]` Remove cluster prior dependency from explanation logic
- `[ ]` Keep clustering only for diversity injection
- `[ ]` Confirm ranking remains stable for sparse catalogs

### 8. Complete Feed Explanation Update

- `[ ]` Replace current `cluster_prior`-based explanation rule
- `[ ]` Add popularity-aware explanation option
- `[ ]` Keep explanations template-only, not taxonomy-heavy
- `[ ]` Make sure category filter does not leak into explanation text

### 9. Complete Phase C Multi-Interest Design Into Code

- `[ ]` Create `user_interests` Qdrant collection
- `[ ]` Add storage payload contract for interest vectors
- `[ ]` Add clustering job over recent liked items
- `[ ]` Compute 2-5 interest centroids
- `[ ]` Persist `feed_weight`, `item_count`, `last_active_at`
- `[ ]` Update primary `user_profiles` vector as weighted blend
- `[ ]` Implement multi-vector candidate retrieval
- `[ ]` Allocate feed slots by `feed_weight`
- `[ ]` Deduplicate merged candidates across interests
- `[ ]` Add lifecycle rules for stale interests

### 10. Operational Hardening

- `[ ]` Add monitoring around profile update latency
- `[ ]` Add monitoring around feed error rate by mode
- `[ ]` Add monitoring around stale profile rate
- `[ ]` Add monitoring around exposure coverage
- `[ ]` Add backfill script for category metadata if source taxonomies change
- `[ ]` Add monitoring around scraper sync success rate vs per-product backend failure rate
- `[ ]` Add monitoring around live category coverage by store
- `[ ]` Add monitoring around archived-vs-active product counts
- `[ ]` Add admin/debug endpoint to inspect a user’s brain state
- `[ ]` Add admin/debug endpoint to force profile rebuild for one user

---

## Developer Verification

Run these after each backend slice:

```bash
cd apps/backend
python -m pytest -p no:cacheprovider tests
python -m compileall src
python -m black --check src
```

Run these after each frontend slice:

```bash
pnpm.cmd --filter @stylipp/web lint
pnpm.cmd --filter @stylipp/web exec tsc --noEmit
```

Run these after schema changes:

```bash
cd apps/backend
alembic upgrade head
```

---

## Manual Tests For You

These are the human checks you can run after each major slice.

### A. Current Slice Verification

- `[ ]` Register a brand-new user
- `[ ]` Call `/auth/me` and confirm the response includes:
  - `interaction_count`
  - `profile_version`
  - `last_profile_update_at`
  - `profile_confidence`
  - `profile_source`
- `[ ]` Complete onboarding
- `[ ]` Call `/auth/me` again and confirm:
  - `onboarding_completed=true`
  - `profile_version >= 1`
  - `profile_confidence > 0`
  - `profile_source="onboarding"`
- `[ ]` Swipe 3-5 products in feed
- `[ ]` Call `/auth/me` again and confirm:
  - `interaction_count` increased
  - `profile_confidence` increased or stayed consistent
- `[ ]` Open feed and use the category chips
- `[ ]` Select `Shoes` and confirm the returned cards are all shoes
- `[ ]` Select `Dresses` and confirm the returned cards are all dresses
- `[ ]` Switch back to `All` and confirm the feed broadens again

### B. Data/Migration Verification

- `[ ]` Confirm the database has the new `users` profile-state columns
- `[ ]` Confirm the database has `products.category` and `products.raw_categories`
- `[ ]` Confirm newly ingested products store a non-empty canonical category where possible
- `[ ]` Confirm Qdrant payload for newly ingested products includes `category`
- `[ ]` Confirm old products only start filtering correctly after resync/reingest
- `[ ]` Confirm products scraped through direct backend ingest preserve `raw_categories`
- `[ ]` Confirm a product page with JSON-LD plus HTML breadcrumbs still lands with categories
- `[ ]` Confirm Hebrew/store-specific category labels map out of `other` when expected

### B2. Scraper Sync Verification

- `[ ]` Scrape one known product and confirm it appears in PostgreSQL through backend ingest without touching a dummy WordPress site
- `[ ]` Confirm scraper updates only successful product hashes after a batch with mixed success/failure
- `[ ]` Force one backend rejection and confirm that product is retried on the next scraper run
- `[ ]` Remove one product from source sitemap and confirm backend marks it archived or inactive
- `[ ]` Confirm archived products do not appear in feed results
- `[ ]` Confirm scraper uses stable source ids where available and does not duplicate products after URL changes

### C. Learning Loop Verification

- `[ ]` Like one product and verify the profile update job is created
- `[ ]` Verify the user vector in Qdrant changes after the job completes
- `[ ]` Dislike one product and verify the vector changes again
- `[ ]` Verify repeated swipes do not crash or block the swipe response
- `[ ]` Verify out-of-order background jobs do not overwrite newer profile state

### D. Feed Mode Verification

- `[ ]` New user with no vector gets `trending` feed instead of error
- `[ ]` User with weak profile gets `hybrid` feed
- `[ ]` Mature user gets `personalized` feed
- `[ ]` `FeedResponse.feed_mode` matches what the UI appears to show
- `[ ]` Category filter works the same in `trending`, `hybrid`, and `personalized`

### E. Exposure Logging Verification

- `[ ]` Open feed and verify visible cards create exposure events
- `[ ]` Swipe a card and verify exposure row gets action + timestamp
- `[ ]` Save a card and verify exposure row reflects save action
- `[ ]` Leave a card visible for several seconds and verify `dwell_ms` is recorded
- `[ ]` Verify no duplicate exposure rows for a single visible card event

### F. Ranking Verification

- `[ ]` Confirm popularity can move items up even when cosine is similar
- `[ ]` Confirm diversity injection still inserts adjacent-cluster items
- `[ ]` Confirm category filtering does not break diversity injection
- `[ ]` Confirm explanations still make sense after popularity replaces cluster prior

### G. Multi-Interest Verification

- `[ ]` Train one user on 2 clearly different styles
- `[ ]` Confirm multiple interest vectors are created
- `[ ]` Confirm the feed contains strong items from both interests
- `[ ]` Confirm stale interests fade when not reinforced

---

## Release Gates

Do not call the brain "done" until all of these are true:

- `[ ]` No-vector users can use the feed immediately
- `[ ]` Swipes update the real profile vector asynchronously
- `[ ]` Feed mode switching works and is visible
- `[ ]` Exposure logging is live and trustworthy
- `[ ]` Category filtering works on real catalog data
- `[ ]` Scraper-to-backend sync preserves categories and does not silently drop failed products
- `[ ]` Removed products are archived or excluded from feed correctly
- `[ ]` Popularity-based ranking replaced `cluster_prior`
- `[ ]` Manual tests in sections A-F plus `B2` all pass
- `[ ]` Multi-interest is either built and passing, or explicitly deferred behind measured gates

---

## Notes For Next Work Session

- Finish scraper/catalog hardening before trusting category quality in production
- Finish environment work first: migrations + reingest
- Finish and deploy feed modes, then build the first real vector-update pipeline
- Do not start multi-interest implementation before the basic learning loop is stable
