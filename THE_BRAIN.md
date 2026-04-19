# Stylipp: The Brain

**Document Purpose:** Architectural blueprint for the Stylipp Recommendation Engine — what's built, what's wrong with it, and the plan to make it genuinely intelligent.

---

## 1. Architecture Overview

Feature-based monolith using **FastAPI**, with strict separation:

- **`router.py`** — HTTP only. Zero logic.
- **`service.py`** — Business logic, vector math, ranking.
- **`schemas.py`** — Pydantic validation.

Two storage systems work in parallel:

| PostgreSQL | Qdrant (Vector DB) |
|---|---|
| Users, Products, Interactions, Clusters | 768-dim FashionSigLIP embeddings |
| Structured metadata | Cosine similarity search |

Three Qdrant collections:
- **`products`** — product vectors + payload (product_id, price, cluster_id)
- **`style_clusters`** — cluster centroid vectors
- **`user_profiles`** — user style vectors

---

## 2. Current State (What's Built)

### A. Cold-Start via Photo Upload

1. User uploads 2 outfit photos
2. FashionSigLIP generates 768-dim embeddings
3. System finds 3 nearest style clusters + 2 diversity clusters
4. Returns 15 calibration items (12 primary + 3 diversity)
5. User swipes like/dislike on each

### B. User Vector (Modified Rocchio)

After calibration, the system computes a single user vector:

```
user_vector = 0.3 * avg(photos) + 1.0 * avg(liked) - 0.25 * avg(disliked)
-> L2 normalized
```

Note: gamma=0.25 (not 0.7 from the original spec) because with only ~5-6 dislikes from calibration, 0.7 was too aggressive and distorted the vector.

### C. Multi-Factor Ranking

```
score = 0.65 * cosine_similarity
      + 0.15 * cluster_prior
      + 0.10 * price_affinity
      + 0.10 * freshness
```

Each factor is min-max normalized within the batch to prevent single-factor dominance.

- **Cosine similarity** — Qdrant vector search against user_vector
- **Cluster prior** — statistical probability per cluster (from K-means pipeline)
- **Price affinity** — log-normal Gaussian against user's price profile
- **Freshness** — exponential decay, 14-day half-life

### D. Diversity Injection

Mandatory 3/20 items from adjacent clusters (4th-5th ranked, not random). Interleaved evenly through the feed.

### E. Image Quality Gate

Before any image enters the system:
- Minimum 400px width/height
- File size 50KB-10MB
- Laplacian variance > 100 (blur detection)

---

## 3. What's Wrong (Honest Assessment)

### Problem 1: The Loop Is Open

```
User swipes -> feedback saved to DB -> ... -> nothing happens
```

The user vector is **frozen** after onboarding. A user who swiped 500 times gets the same quality recommendations as after the first 15. The system does not learn from ongoing behavior. **This is the single biggest problem.**

### Problem 2: Onboarding Is a Wall

The current flow requires 2 photo uploads + 15 calibration swipes before the user sees any real feed. This is ~3 minutes of effort before any value.

Comparison:
- **TikTok** — 0 seconds. Shows content immediately. Learns from behavior.
- **Pinterest** — ~10 seconds. Pick 5 topics. See feed.
- **Stylipp** — ~3 minutes. Upload photos. Wait for processing. Swipe 15 cards. Then see feed.

Every step in onboarding is a drop-off point. Photo upload on mobile is especially high friction.

### Problem 3: Single Vector = Averaged-Out Taste

A user who likes both streetwear AND formal dresses gets a vector pointing to "neither." Recommendations end up mediocre across all styles instead of excellent in any one.

Real users have 2-5 distinct style interests. One vector cannot represent this.

### Problem 4: Clustering Pipeline Overhead

The cluster_prior contributes 15% to the ranking score but requires:
- K-means + silhouette analysis pipeline
- ClusterRepository + StyleCluster model
- Qdrant `style_clusters` collection
- cluster_id payload on every product
- Manual rebuild endpoint

A simple engagement/popularity score from real user interactions would provide similar signal with zero infrastructure.

### Problem 5: No Exposure Logging

The system stores actions (like/dislike/save) but not impressions. Without tracking what was shown, in what position, and whether the user even saw it:
- Popularity metrics are biased toward items shown first
- Can't distinguish "user didn't like it" from "user never saw it"
- Can't measure true engagement rate (actions / impressions)
- Position bias will silently corrupt every metric

### Problem 6: No Feed Mode Handling

`feed_service.py` raises `ValueError` if no user vector exists. There is no graceful fallback. This blocks the zero-friction start and makes the system fragile for any edge case where a profile is missing or corrupted.

---

## 4. The Plan (Priority Order)

### Phase A: Close the Learning Loop

**Goal:** Every swipe makes the next feed better.

**A1: Profile State Model**

The current User model only stores `onboarding_completed` and `price_profile`. For a learning system, add:

```python
# On User model (PostgreSQL):
interaction_count: int          # total swipes, drives learning rate
profile_version: int            # incremented on each vector update
last_profile_update_at: datetime # detect stale profiles
profile_confidence: float       # 0.0 (new) to 1.0 (mature)
profile_source: str             # "onboarding" | "auto_coldstart" | "learning" | "photo_boosted"

# Confidence formula:
# confidence = min(1.0, log(1 + interaction_count) / log(1 + 200))
# Reaches ~0.5 at 14 interactions, ~0.8 at 60, reaches 1.0 at 200
```

This is the foundation. Learning rate, feed mode transitions, and guardrails all depend on knowing the profile's maturity.

**A2: Learning Pipeline Boundary**

Critical architectural decision: **decouple feedback writes from profile updates.**

```
Swipe request:
  1. Write UserInteraction to PostgreSQL     -- sync, fast (~2ms)
  2. Write ExposureLog if needed             -- sync, fast
  3. Enqueue profile update                  -- async, decoupled
  4. Return 201 to client                    -- instant response

Background worker (or FastAPI BackgroundTask for MVP):
  1. Dequeue profile update job
  2. Compute new vector
  3. Upsert to Qdrant                        -- latency here is invisible
  4. Update profile metadata in PostgreSQL
```

Why: Qdrant upsert latency (~5-20ms) should never be in the swipe response path. If Qdrant is slow or down, swipes still work. Profile updates catch up.

For MVP: `BackgroundTasks` in FastAPI is enough. For scale: ARQ or Celery.

**Crash recovery:** If the process dies after writing feedback but before updating the profile, the profile becomes stale but not corrupted — the old vector is still valid, just slightly behind. On next startup (or next successful update), the periodic full rebuild (A4) will reconcile. No data is lost because feedback is already committed to PostgreSQL. This is acceptable for MVP; a durable queue (ARQ + Redis) eliminates the gap entirely.

**Update ordering:** Profile updates must be applied in sequence. Each update reads `profile_version` before writing and increments it atomically. If a background job reads version N but the profile is already at version N+1 (a newer update landed first), the job is discarded — the newer state wins. This prevents slow jobs from overwriting fresher profiles.

**A3: Incremental Vector Update**

Instead of recomputing from full history, update incrementally:

```python
# On like:
new_vector = normalize((1 - lr) * user_vector + lr * product_vector)

# On dislike:
new_vector = normalize((1 - lr) * user_vector - gamma * product_vector)

# Learning rate schedule (driven by profile_confidence):
#   confidence < 0.3 (new, < ~15 interactions): lr = 0.15
#   confidence 0.3-0.7 (moderate, 15-60):       lr = 0.08
#   confidence > 0.7 (mature, 60+):              lr = 0.03
#
# gamma (negative weight): 0.05
#   Light push away, not aggressive
#   Prevents dislike-dominated drift
```

**A4: Guardrails for Online Learning**

Online updates without safety rails = profile corruption.

```python
# Per-swipe movement cap:
max_delta = 0.15  # cosine distance cap per update
if cosine_distance(old_vector, new_vector) > max_delta:
    new_vector = slerp(old_vector, new_vector, max_delta / actual_delta)

# Burst detection:
# If 10+ dislikes in a row, dampen gamma by 0.5x
# Prevents rage-swiping from destroying the profile

# Stale interest decay:
# Interests not reinforced in 30 days lose weight gradually
# Prevents abandoned interests from occupying feed slots forever

# Periodic full rebuild (weekly or every 200 interactions):
# Recompute vector from full interaction history
# Corrects any drift accumulated from incremental updates
# Profile version bumps, confidence recalculated
```

**A5: Category Metadata and Filtering**

The user's style vector works across all product types — it captures taste, not category. This enables a powerful UX: "show me only shoes that match my style." The vector stays the same, only the search scope changes.

**Why in Phase A:** Category data comes free from the ingestion pipeline (WooCommerce already provides it). Storing it now means the feed can support filtering from day one. Without it, we'd need a costly backfill later.

```python
# Product model -- two new fields:
category_slug: str       # canonical: "shoes" | "tops" | "pants" | "dresses" | ...
raw_categories: list[str] | None  # original WooCommerce categories, preserved for debugging/backfills

# Qdrant product payload -- add to existing payload:
{
    "product_id": "...",
    "price": 89.90,
    "cluster_id": 7,
    "category": "shoes"     # <-- canonical slug, used for filtering
}

# Feed API -- optional query parameter, works in ALL feed modes:
# GET /api/feed/                   -> all products matching user style
# GET /api/feed/?category=shoes    -> only shoes matching user style
# GET /api/feed/?category=dresses  -> only dresses matching user style
#
# In TRENDING mode:  filters trending items by category
# In HYBRID mode:    filters both personalized and trending halves by category
# In PERSONALIZED:   filters personalized results by category

# Qdrant filter -- one additional FieldCondition when category param is present:
if category:
    filter.must.append(FieldCondition(key="category", match=MatchValue(value=category)))
```

**Category source:** WooCommerce product categories are already fetched by `WooCommerceClient` but discarded by `ProductTransformer`. Fix: extract the primary category from `WooProduct.categories`, normalize to a canonical slug, and store both the slug (`Product.category_slug`) and raw categories (`Product.raw_categories`) on the product. Only the canonical slug goes into the Qdrant payload for filtering.

**Canonical category set:** Start small and merge aggressively. 7-10 categories max. Unknown or ambiguous categories default to `"other"`. The set can expand later but should never exceed ~15 — too many categories defeats the purpose.

**Important boundaries:**

- **Category does not affect the user vector.** Filtering by "shoes" narrows retrieval only. The user vector is not updated or modified by category selection. If the user likes a shoe, the vector update comes from the like — not from the fact that the category was "shoes."
- **Multi-category products are intentionally simplified.** Some items belong to multiple WooCommerce categories (e.g., "ankle boots" tagged as both "shoes" and "boots"). For MVP, we pick the first/primary category. The raw categories are preserved in `raw_categories` for future multi-label support or backfills. This will be wrong sometimes — that is acceptable at this stage.

**A6: Rolling Price Profile**

Replace the one-time IQR calculation with exponential moving average:

```python
# After each like:
alpha = 0.1  # smoothing factor
new_median = alpha * liked_price + (1 - alpha) * current_median
# Bounds adjust proportionally
```

**Impact:** The system becomes alive. Users feel "it's getting better the more I use it."

---

### Phase B: Zero-Friction Start

**Goal:** Value in 0 seconds, not 3 minutes.

**B1: Feed Mode State Machine**

Explicit states with clear transitions — the feed never errors, it adapts:

```
TRENDING --[10+ swipes]--> HYBRID --[confidence > 0.5]--> PERSONALIZED

TRENDING:         No vector, no interactions.
                  Popular items diversified by cluster.
                  Ranked by time-decayed engagement score.

HYBRID:           Has vector but low confidence.
                  50% personalized (cosine against weak vector)
                  + 50% trending (safety net while profile is thin).
                  Blend ratio shifts toward personalized as confidence grows.

PERSONALIZED:     Confident profile (60+ interactions).
                  Full multi-factor ranking against mature vector.
                  Diversity injection from adjacent clusters.
                  Trending items still injected at low rate (5%) for discovery.
```

Transition thresholds stored in config, not hardcoded.

**Response contract:** `FeedResponse.feed_mode` returns the active mode as a string (`"trending"` | `"hybrid"` | `"personalized"`). This lets the frontend adapt UI — e.g., show a "personalizing..." indicator in hybrid mode, or hide it once personalized.

**B2: Popular/Trending Feed for New Users**

No vector? No problem. Serve the most-engaged products diversified by cluster:

```python
# For users in TRENDING mode:
# 1. Query UserInteraction for like/save counts per product
# 2. Apply time-decayed popularity (same 14-day half-life)
# 3. Diversify across clusters
# 4. Return as feed
# Falls back to newest products if no interaction data exists
```

**B3: Auto Cold-Start from Swipes**

After ~10 swipes on trending feed, compute initial vector automatically:

```python
# Trigger: interaction_count >= 10 AND profile_source is None
# 1. Fetch liked product vectors from Qdrant
# 2. Fetch disliked product vectors
# 3. user_vector = normalize(avg(liked) - 0.25 * avg(disliked))
# 4. Store in Qdrant user_profiles
# 5. Set profile_source = "auto_coldstart"
# 6. Feed transitions to HYBRID mode
```

No photo upload required. The user doesn't even know it happened.

**B4: Photos as Optional Boost**

Move photo upload to Settings as an optional "improve your recommendations" feature. If provided, blend into the vector:

```python
# user_vector = normalize(0.2 * avg(photos) + 0.8 * current_vector)
# profile_source updates to "photo_boosted"
```

**Impact:** Onboarding becomes invisible. Users see value immediately.

---

### Phase C: Multi-Interest Vectors

**Status:** Design spec only. Not a build spec yet — details will be refined when Phase A/B metrics prove the learning loop works.

**Gate:** Phase C does NOT start until Phase A and B show measurable improvement:
- Like rate improved by 10%+ relative to pre-Phase-A baseline
- At least 50% of active users reach PERSONALIZED mode within 48h
- Learning loop is stable (no profile corruption incidents for 2+ weeks)

If these gates aren't met, the problem is in the loop, not in single-vs-multi vectors. Fix A/B first.

**Goal:** Understand that users are complex. Recommend the best streetwear AND the best formal wear, not a compromise.

**C1: Storage Shape**

New Qdrant collection `user_interests` (separate from `user_profiles`):

```python
# Collection: user_interests
# Point ID format: "{user_id}_{interest_index}" (e.g., "abc123_0", "abc123_1")
#
# Vector: 768-dim (interest centroid)
#
# Payload:
{
    "user_id": "abc123",
    "interest_index": 0,
    "item_count": 42,          # how many likes in this interest
    "last_active_at": "2026-04-01T...",
    "confidence": 0.8,         # silhouette score of this cluster
    "feed_weight": 0.45,       # proportional allocation in feed
    "label": null               # optional: auto-generated or user-named
}

# user_profiles collection REMAINS as the "primary" blended vector
# for backward compatibility and quick single-vector search
# user_interests is the detailed multi-interest layer
```

**C2: Interest Discovery**

Periodically cluster the user's liked items into 2-5 interest groups:

```python
# Trigger: every 30 new likes OR weekly
# 1. Collect user's last 100 liked product vectors
# 2. K-means with k = 2..5, pick best by silhouette score
# 3. Each cluster centroid = one "interest vector"
# 4. Upsert to Qdrant user_interests collection
# 5. Tag each with: item_count, last_active, feed_weight
# 6. Update primary vector in user_profiles as weighted average
```

**C3: Multi-Vector Feed Generation**

```python
# For each interest vector:
#   - Search Qdrant for candidates
#   - Allocate feed slots proportional to feed_weight
#     (interest with 40 likes gets more slots than one with 10)
# Merge, deduplicate, apply ranking
# Result: excellent recs in EACH style, not mediocre in all
```

**C4: Interest Evolution**

Interests shift. Re-cluster periodically. New interests emerge naturally when a user starts liking a new style. Old interests fade via time decay on `last_active_at`. Interests with zero activity for 30+ days get their `feed_weight` halved each period until dropped.

**Impact:** Recommendations feel like "this app really gets me" instead of "this is sort of okay."

---

### Phase D: Simplify Ranking

**Goal:** Less infrastructure, same or better results.

**D1: Replace cluster_prior with engagement score**

Time-decayed popularity with Bayesian smoothing to handle small sample sizes:

```python
# Raw popularity:
raw_score = sum(decay(t) for t in item_like_timestamps)

# Bayesian smoothing (Wilson-like prior):
# Prevents items with 2 likes / 2 impressions from beating
# items with 200 likes / 1000 impressions
global_like_rate = total_likes / total_impressions  # ~0.35
smoothed = (raw_likes + prior_weight * global_like_rate) /
           (raw_impressions + prior_weight)
# prior_weight = 20 (equivalent to 20 "virtual" impressions)

# Final popularity score: normalized to [0, 1]
popularity = smoothed / max_smoothed_in_batch
```

New ranking formula:
```
score = 0.70 * cosine_similarity
      + 0.15 * popularity          # was cluster_prior
      + 0.10 * price_affinity
      + 0.05 * freshness
```

**D2: Explanation Layer Update**

Current explanation logic in `router.py` depends on `cluster_prior_score`. When cluster_prior exits the ranking formula:

```python
# Old logic:
# if price_score > cluster_score and price_score > cosine_score: "price range"
# elif cluster_score > cosine_score: "matches your style"
# else: "similar to recent likes"

# New logic:
# if price_score dominant: "Within your usual price range"
# elif popularity_score dominant: "Trending in your style"
# else: "Similar to your recent likes"
```

**D3: Keep clustering for diversity only**

Clusters remain useful for diversity injection (picking "adjacent but different" items). But they exit the ranking formula.

**D4: Future — Learned Weights**

With enough data (500+ users), learn optimal weights from engagement signals.

**Impact:** Removes the heaviest infrastructure piece from the critical path while maintaining recommendation quality.

---

## 5. Exposure Logging

Track what was shown, not just what was acted on. Without this, every metric is biased.

### Schema

**Decision:** ExposureLog is a **separate table**, not an extension of UserInteraction. Reasons: (1) impressions outnumber actions 3-5x, mixing them inflates the interactions table; (2) different query patterns — exposure queries are analytical, interaction queries are transactional; (3) ExposureLog can be bulk-inserted from batched frontend events without touching the interaction write path.

```python
# New model: ExposureLog (separate table)
class ExposureLog:
    id: UUID
    user_id: UUID
    product_id: UUID
    session_id: str              # groups a feed session
    feed_mode: str               # "trending" | "hybrid" | "personalized"
    position: int                # 0-indexed position in feed
    shown_at: datetime           # when the card was rendered
    action: str | None           # "like" | "dislike" | "save" | None (skipped/unseen)
    action_at: datetime | None   # when action occurred (None if no action)
    dwell_ms: int | None         # time spent on this card before action
```

### Why Each Field Matters

- **session_id** — groups a scroll session. Without it, can't compute session depth
- **position** — items at position 0 get more engagement than position 15. Position bias correction requires this
- **feed_mode** — a like in trending mode has different meaning than in personalized mode
- **shown_at** vs **action_at** — the gap is dwell time. High dwell + dislike = different signal than instant dislike
- **dwell_ms** — implicit interest signal. >3s dwell without action = mild interest. <0.5s swipe = no interest

### Implementation Note

Log exposure when the card becomes the top card in the stack (visible to user), not when the feed is fetched. Frontend sends exposure events. Batch them — don't send one HTTP request per card.

---

## 6. Richer Feedback Signals

Current action space: `like | dislike | save`

### Planned Signal Expansion

| Signal | Value | When to Add |
|---|---|---|
| `dwell_ms` | Implicit interest even without action | Phase A (easy, high value) |
| `opened_product` | Clicked "View" link — strong intent | Phase A (easy, high value) |
| `undo` | Already built but not logged as signal | Phase A (free, already exists) |
| `scroll_depth` | How far into feed user scrolled | Phase B (session quality metric) |
| `shared` | Strong positive signal | Future (no sharing feature yet) |

### Signal Weights for Learning

```python
# When updating user vector, weight by signal strength:
signal_weights = {
    "like": 1.0,
    "save": 1.5,           # save > like (deliberate action)
    "opened_product": 0.8, # clicked through = interested
    "dislike": -1.0,
    "undo_like": -0.5,     # changed mind = mild negative
    "undo_dislike": 0.5,   # changed mind = mild positive
}
# dwell_ms modulates: >3s dwell multiplies weight by 1.2x
```

---

## 7. Execution Order

```
Phase A (Learning Loop)    -- The system learns. Without this, nothing else matters.
Phase B (Zero Friction)    -- Users see value instantly. Removes the biggest UX barrier.
Phase D (Simplify Ranking) -- Less code, less maintenance, same results.
Phase C (Multi-Interest)   -- Gated on A/B metrics. The quality leap that makes Stylipp special.
```

---

## 8. Core Product Principle: Don't Search, Find

Traditional fashion shopping: filter by category, sort by price, scroll through 3,000 results, hope something catches your eye.

Stylipp: tell the system what type of item you want, and it shows you exactly the ones you'll love.

```
ASOS / ZARA:                          Stylipp:
  Filter "shoes"                        Filter "shoes"
  -> 3,000 results                      -> 20 results, ranked by "how much is this YOU"
  Sort by "newest" / "price"            No sorting needed -- best match first
  Scroll for 30 minutes                 Find what you want in under a minute
  Maybe find something                  Every item feels relevant
```

This works because the user's style vector is style-aware, not category-aware. FashionSigLIP encodes visual taste -- minimalist, bold, streetwear, elegant -- and that taste applies equally to shoes, tops, and dresses.

Category filtering (Phase A5) scopes the search. The style vector does the ranking. Together: "show me only shoes that match my taste." No search bar. No keywords. No endless scrolling.

---

## 9. What NOT to Change

These are solid and should stay:

- **FashionSigLIP** (Marqo) — Best-in-class fashion embeddings, Apache 2.0
- **Qdrant** — Fast, async, great filtering, self-hosted
- **PostgreSQL + async SQLAlchemy** — Proven, reliable
- **Quality Gate** — Prevents garbage data from polluting vectors
- **Feature folder structure** — Clean separation, easy to navigate
- **Diversity injection pattern** — Prevents echo chambers

---

## 9. Success Metrics

### Product Metrics

How to know the Brain is working for users:

| Metric | Bad | Good | Great |
|---|---|---|---|
| Like rate (likes / total swipes) | < 20% | 30-40% | > 45% |
| Session depth (swipes per session) | < 10 | 20-40 | > 50 |
| D7 retention | < 10% | 20-30% | > 40% |
| Time to first like | > 30 swipes | 5-15 swipes | < 5 swipes |
| Save rate | < 2% | 5-8% | > 10% |

These metrics should improve measurably after each phase ships.

### Operational Metrics

How to know the Brain is healthy:

| Metric | What It Tells You | Alert Threshold |
|---|---|---|
| Profile update latency (p95) | Is the learning pipeline keeping up? | > 500ms |
| Cold-start to personalized conversion | Are users reaching personalized mode? | < 50% within 24h |
| Stale profile rate | % of active users with no update in 7d | > 20% |
| Diversity hit rate | Are diversity items actually being shown? | < 10% of feed |
| Profile confidence distribution | Is the user base maturing? | Median < 0.3 after 30d |
| Vector drift per day | Are profiles changing too fast or too slow? | > 0.3 cosine/day |
| Exposure log coverage | % of shown items with exposure records | < 90% |
| Feed error rate | Failed feed generations / total requests | > 1% |
