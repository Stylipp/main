# Phase 5: Feed Generation & Ranking - Research

**Researched:** 2026-03-12
**Domain:** Multi-factor recommendation ranking with Qdrant vector search
**Confidence:** HIGH

<research_summary>
## Summary

Researched the architecture and implementation patterns for building a multi-factor feed ranking system on top of Qdrant v1.7.4 with FastAPI. The system must combine cosine similarity (65%), cluster prior (15%), price affinity (10%), and freshness (10%) into a unified score, with mandatory diversity injection (3/20 items from adjacent clusters).

**Critical finding:** Qdrant v1.7.4 does NOT support the Query API (v1.10+), Score-Boosting Reranker (v1.14+), or fusion methods (RRF/DBSF). All multi-factor ranking must happen application-side in Python after candidate retrieval from Qdrant. This is the standard two-stage pipeline pattern (candidate generation → application-side re-ranking) used by production recommendation systems.

The existing cold-start service already implements the diversity injection pattern correctly (17 primary + 3 diversity items, interleaved). The feed service should follow this same pattern for warm-start users, replacing photo-based nearest-cluster matching with user-vector-based similarity search.

**Primary recommendation:** Two-stage pipeline — Qdrant retrieves ~100 candidates via user vector cosine search with seen-item exclusion, then Python re-ranks with weighted multi-factor scoring and diversity injection. Cache pre-ranked batches in Redis for pagination.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| qdrant-client | >=1.7,<1.13 | Vector similarity search for candidates | Already in project, handles Stage 1 retrieval |
| redis (aioredis) | Already in stack | Feed batch caching + seen items tracking | Already in project, O(1) set operations |
| numpy | Already in stack | Score normalization and vector operations | Already used for embeddings |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| math (stdlib) | N/A | Exponential decay, Gaussian scoring | Price affinity + freshness calculations |
| uuid (stdlib) | N/A | Cursor token generation | Opaque pagination cursors |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Application-side ranking | Qdrant Score-Boosting Reranker | Requires Qdrant v1.14+, would need server upgrade |
| Application-side ranking | Qdrant Query API + fusion | Requires Qdrant v1.10+, would need server upgrade |
| Redis seen-items Set | Qdrant has_id must_not filter only | Redis adds TTL expiry for seen items, reduces Qdrant filter size |
| Redis feed cache | PostgreSQL materialized view | Redis is faster for ephemeral feed data with TTL |
| rerankers/RankLLM Python libs | Custom weighted scoring | ML-model rerankers designed for NLP/RAG, not weighted feature scoring — overkill and wrong tool |

**No new dependencies needed.** The existing stack (qdrant-client, Redis, numpy, FastAPI) handles everything.
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
src/features/feed/
├── router/
│   └── router.py          # GET /feed endpoint with pagination
├── service/
│   ├── feed_service.py     # Orchestrates candidate retrieval + ranking
│   ├── ranking_service.py  # Multi-factor scoring logic
│   └── feed_cache.py       # Redis feed batch caching + seen items
├── schemas/
│   └── schemas.py          # FeedRequest, FeedResponse, FeedItem
└── utils/
    └── scoring.py          # Score normalization helpers
```

### Pattern 1: Two-Stage Candidate Generation → Re-Ranking
**What:** Retrieve broad candidates from Qdrant, then score and re-rank in application code
**When to use:** Always — this is the standard recommendation system architecture
**Why:** Vector search handles approximate nearest neighbors efficiently (Stage 1), but business logic (price, freshness, diversity) requires application-side scoring (Stage 2)

```python
# Stage 1: Candidate Generation (Qdrant)
candidates = await qdrant_client.search(
    collection_name="products",
    query_vector=user_vector,       # 768-dim from user_profiles collection
    query_filter=models.Filter(
        must_not=[
            models.HasIdCondition(has_id=seen_product_ids)  # Exclude seen items
        ],
        must=[
            models.FieldCondition(
                key="price",
                range=models.Range(
                    gte=price_min * 0.5,   # Generous price filter
                    lte=price_max * 2.0,   # Don't exclude borderline items
                )
            )
        ]
    ),
    limit=100,  # Oversample 5x target (20 items)
    score_threshold=0.3,  # Floor for minimum relevance
)

# Stage 2: Application-Side Re-Ranking
scored_items = []
for candidate in candidates:
    cosine_score = candidate.score  # Already 0-1 for cosine
    prior_score = get_cluster_prior(candidate.payload["cluster_id"])
    price_score = compute_price_affinity(candidate.payload["price"], user_price_profile)
    freshness_score = compute_freshness(candidate.payload["created_at"])

    final_score = (
        0.65 * cosine_score +
        0.15 * prior_score +
        0.10 * price_score +
        0.10 * freshness_score
    )
    scored_items.append((candidate, final_score))

scored_items.sort(key=lambda x: x[1], reverse=True)
```

### Pattern 2: Pre-Computed Feed Batches with Redis Caching
**What:** Generate a full batch (e.g., 60 items) on first request, cache in Redis, paginate from cache
**When to use:** When Qdrant search is the bottleneck and users request feed in small pages (20 items)
**Why:** Avoids re-running expensive vector search + ranking on every page request

```python
# Generate batch on first request or cache miss
FEED_BATCH_SIZE = 60  # 3 pages worth
FEED_CACHE_TTL = 300  # 5 minutes

async def get_feed(user_id: str, cursor: Optional[str] = None) -> FeedResponse:
    cache_key = f"feed:{user_id}"

    if cursor:
        # Retrieve cached batch, return next page
        cached = await redis.get(cache_key)
        if cached:
            batch = deserialize(cached)
            page = batch[cursor_offset:cursor_offset + PAGE_SIZE]
            return FeedResponse(items=page, next_cursor=next_cursor)

    # Generate fresh batch
    candidates = await retrieve_candidates(user_id, limit=100)
    ranked = rank_candidates(candidates, user_profile)
    diversity_injected = inject_diversity(ranked, FEED_BATCH_SIZE)

    # Cache batch
    await redis.setex(cache_key, FEED_CACHE_TTL, serialize(diversity_injected))

    # Mark items as seen
    product_ids = [item.product_id for item in diversity_injected]
    await redis.sadd(f"seen:{user_id}", *product_ids)

    page = diversity_injected[:PAGE_SIZE]
    return FeedResponse(items=page, next_cursor=encode_cursor(PAGE_SIZE))
```

### Pattern 3: Diversity Injection via Cluster Slot Reservation
**What:** Reserve 3/20 slots for items from adjacent (non-top) clusters, interleave them
**When to use:** Every feed generation — mandatory per PROJECT.md
**Why:** Prevents echo chambers, introduces serendipity

```python
# Already proven in cold_start_service.py — adapt for warm-start
def inject_diversity(ranked_items: list, target_count: int) -> list:
    PRIMARY_RATIO = 17 / 20  # 85% from top clusters
    DIVERSITY_RATIO = 3 / 20  # 15% from adjacent clusters

    primary_count = int(target_count * PRIMARY_RATIO)
    diversity_count = target_count - primary_count

    primary = ranked_items[:primary_count]
    # Diversity items: ranked by score but from non-top clusters
    diversity = [item for item in ranked_items[primary_count:]
                 if item.cluster_id not in top_cluster_ids][:diversity_count]

    # Interleave: insert diversity item every ~6 positions
    result = []
    div_idx = 0
    for i, item in enumerate(primary):
        result.append(item)
        if (i + 1) % 6 == 0 and div_idx < len(diversity):
            result.append(diversity[div_idx])
            div_idx += 1

    # Append remaining diversity items
    result.extend(diversity[div_idx:])
    return result[:target_count]
```

### Anti-Patterns to Avoid
- **Re-running Qdrant search per page:** Expensive and results change between pages. Cache the batch.
- **Global score normalization:** Use per-batch min-max normalization, not global stats that drift.
- **Appending diversity items at end:** Users never see them if they stop scrolling. Interleave instead.
- **Hardcoded score thresholds:** Cosine similarity distributions vary by user. Use relative ranking, not absolute thresholds.
- **Blocking on Redis cache misses:** Generate feed synchronously on first request, cache for subsequent pages.
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Vector nearest-neighbor search | Custom distance calculations | Qdrant `search()` with cosine | HNSW index is orders of magnitude faster than brute-force |
| Seen items deduplication | Custom SQL tracking table | Redis Set (`SADD`/`SISMEMBER`) per user | O(1) operations, TTL auto-cleanup, already in stack |
| Feed batch caching | Custom in-memory cache | Redis `SETEX` with TTL | Survives process restarts, shared across workers |
| Score normalization | Custom normalization code | numpy `(x - min) / (max - min)` or simple arithmetic | Well-tested, handles edge cases (all same score) |
| Cursor encoding | Custom cursor format | Base64-encoded JSON `{offset, batch_id}` | Standard pattern, opaque to client |
| Price range filtering | Post-retrieval price filter | Qdrant payload `Range` filter | Reduces candidate set at search time, faster |

**Key insight:** The multi-factor ranking itself IS the custom logic — it's a simple weighted sum that doesn't justify a library. Everything else (vector search, caching, filtering, seen-item tracking) should use existing infrastructure. The scoring formulas (Gaussian decay, exponential decay) are 3-5 lines of math each — simpler than importing a dependency.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Score Scale Mismatch
**What goes wrong:** Combining raw cosine similarity (0-1) with cluster prior (0.001-0.05) and freshness (0-1) produces rankings dominated by cosine similarity
**Why it happens:** Different scoring factors operate on different scales and distributions
**How to avoid:** Normalize ALL factors to [0,1] using min-max scaling within each batch before applying weights
**Warning signs:** Ranking barely changes when adjusting weights; one factor always dominates

```python
# WRONG: Raw scores
final = 0.65 * cosine + 0.15 * prior + 0.10 * price + 0.10 * freshness

# RIGHT: Normalized scores
cosine_norm = (cosine - min_cosine) / (max_cosine - min_cosine + 1e-8)
prior_norm = (prior - min_prior) / (max_prior - min_prior + 1e-8)
# ... then combine normalized scores
```

### Pitfall 2: Empty Feed / Insufficient Candidates
**What goes wrong:** User exhausts all products in their style clusters, feed returns empty
**Why it happens:** Small catalog (300-500 products) + active user = quickly runs out of unseen items
**How to avoid:** Implement fallback strategy — if primary search returns < threshold, widen search (lower score_threshold, remove cluster filter, or include seen items with "revisit" flag)
**Warning signs:** Feed API returning fewer items than requested page size

### Pitfall 3: Stale Feed Cache Mismatch
**What goes wrong:** User swipes on items, but cached feed still shows them
**Why it happens:** Feed batch cached in Redis doesn't reflect real-time swipe actions
**How to avoid:** On swipe action, remove item from cached batch OR invalidate cache. Don't serve already-swiped items.
**Warning signs:** Users seeing items they already swiped on

### Pitfall 4: Cold-Start vs Warm-Start Discontinuity
**What goes wrong:** Feed quality drops sharply after onboarding ends and warm-start kicks in
**Why it happens:** Cold-start uses cluster-based matching (proven), warm-start uses different logic with untested weights
**How to avoid:** Warm-start should produce similar quality to cold-start for new users. Test with same user vectors. Consider blending: for users with < 30 interactions, mix cold-start and warm-start results.
**Warning signs:** Users who complete onboarding but stop engaging after seeing first warm feed

### Pitfall 5: Diversity Items Tanking Engagement
**What goes wrong:** Diversity items have much lower scores, users notice quality drop
**Why it happens:** Items from non-top clusters are inherently less similar to user preferences
**How to avoid:** Diversity items should still meet minimum quality threshold. Pick top-scoring items from adjacent clusters (4th-5th ranked), not random clusters. Already done correctly in cold_start_service.py.
**Warning signs:** Consistently low engagement on every 6th item in feed

### Pitfall 6: Price Filter Too Aggressive
**What goes wrong:** Feed excludes good matches because price is slightly outside user's range
**Why it happens:** Tight price filter in Qdrant query removes candidates before scoring
**How to avoid:** Use generous Qdrant price filter (0.5x min to 2x max), then let price_affinity scoring handle fine-grained ranking. The score weight (10%) naturally deprioritizes without hard-excluding.
**Warning signs:** Feed consistently has fewer items than expected; good style matches missing
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from existing codebase and Qdrant documentation:

### Multi-Factor Scoring Function
```python
import math
from datetime import datetime, timezone

# Constants
WEIGHT_COSINE = 0.65
WEIGHT_PRIOR = 0.15
WEIGHT_PRICE = 0.10
WEIGHT_FRESHNESS = 0.10

# 14-day half-life: λ = ln(2) / 14
FRESHNESS_LAMBDA = math.log(2) / 14  # ≈ 0.0495

def compute_freshness_score(created_at: datetime) -> float:
    """Exponential decay with 14-day half-life.

    Score = e^(-λ * days_old)
    At 0 days: 1.0, at 14 days: 0.5, at 28 days: 0.25
    """
    now = datetime.now(timezone.utc)
    days_old = (now - created_at).total_seconds() / 86400
    return math.exp(-FRESHNESS_LAMBDA * max(days_old, 0))


def compute_price_affinity(
    product_price: float,
    price_median: float,
    price_std: float,
) -> float:
    """Gaussian decay centered on user's median price.

    Uses log-space to avoid linear bias toward expensive items.
    Score = e^(-(log(price) - log(median))^2 / (2 * log_σ^2))
    """
    if price_median <= 0 or product_price <= 0:
        return 0.5  # Neutral if no price data

    log_price = math.log(product_price)
    log_median = math.log(price_median)
    # Use price_std in log-space, with floor to avoid division by zero
    log_sigma = math.log(max(price_std, price_median * 0.3)) if price_std > 0 else 0.5
    log_sigma = max(log_sigma, 0.1)  # Floor

    exponent = -((log_price - log_median) ** 2) / (2 * log_sigma ** 2)
    return math.exp(exponent)


def normalize_scores(scores: list[float]) -> list[float]:
    """Min-max normalize scores to [0, 1]."""
    if not scores:
        return scores
    min_s = min(scores)
    max_s = max(scores)
    range_s = max_s - min_s
    if range_s < 1e-8:
        return [0.5] * len(scores)  # All equal → neutral
    return [(s - min_s) / range_s for s in scores]
```

### Qdrant Search with Seen-Item Exclusion (v1.7.4 compatible)
```python
from qdrant_client import models

async def retrieve_candidates(
    qdrant_client,
    user_vector: list[float],
    seen_ids: list[str],
    price_min: float,
    price_max: float,
    limit: int = 100,
) -> list:
    """Stage 1: Retrieve candidates from Qdrant with filters."""

    must_not = []
    if seen_ids:
        must_not.append(models.HasIdCondition(has_id=seen_ids))

    must = []
    if price_min > 0 and price_max > 0:
        must.append(models.FieldCondition(
            key="price",
            range=models.Range(
                gte=price_min * 0.5,   # Generous: 50% below min
                lte=price_max * 2.0,   # Generous: 200% above max
            ),
        ))

    query_filter = models.Filter(must=must, must_not=must_not) if must or must_not else None

    results = await qdrant_client.search(
        collection_name="products",
        query_vector=user_vector,
        query_filter=query_filter,
        limit=limit,
        score_threshold=0.2,  # Minimum cosine similarity floor
    )

    return results
```

### Redis Seen-Items Tracking
```python
SEEN_TTL = 86400 * 7  # 7 days — after a week, items can reappear

async def mark_seen(redis, user_id: str, product_ids: list[str]):
    """Add products to user's seen set with TTL."""
    key = f"seen:{user_id}"
    if product_ids:
        await redis.sadd(key, *product_ids)
        await redis.expire(key, SEEN_TTL)

async def get_seen_ids(redis, user_id: str) -> list[str]:
    """Get all seen product IDs for a user."""
    key = f"seen:{user_id}"
    members = await redis.smembers(key)
    return list(members)
```

### Cursor-Based Feed Pagination
```python
import base64
import json

def encode_cursor(offset: int, batch_id: str) -> str:
    """Encode pagination cursor as opaque base64 token."""
    data = json.dumps({"o": offset, "b": batch_id})
    return base64.urlsafe_b64encode(data.encode()).decode()

def decode_cursor(cursor: str) -> tuple[int, str]:
    """Decode cursor to (offset, batch_id)."""
    data = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
    return data["o"], data["b"]
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-stage vector search | Two-stage: retrieve + re-rank | Industry standard | Allows business logic without custom vector DB features |
| Qdrant basic search API | Qdrant Query API + fusion (v1.10+) | 2024 | Unified API for hybrid search, but requires v1.10+ |
| Application-side reranking | Qdrant Score-Boosting Reranker (v1.14+) | 2025 | Server-side formula reranking, but requires v1.14+ |
| Manual score combination | Weighted RRF (v1.17+) | 2025 | Per-prefetch importance weights, but requires v1.17+ |
| Offset pagination | Cursor-based pagination | Standard | Stable for dynamic feeds, no skip/duplicate issues |
| SQL seen-items table | Redis Set with TTL | Standard | O(1) operations, auto-cleanup |

**New tools/patterns to consider:**
- **Qdrant upgrade path**: Upgrading from v1.7.4 to v1.14+ would unlock server-side score boosting, eliminating application-side re-ranking. Consider for Phase 12 (Performance & Caching).
- **Redis Bloom Filter**: For very large catalogs (10K+ products), Bloom filter is more memory-efficient than Set for seen-item tracking. Not needed at 300-500 products.
- **DBSF fusion**: Distribution-Based Score Fusion (Qdrant v1.11+) handles score normalization automatically. Would simplify multi-factor ranking if Qdrant upgraded.

**Deprecated/outdated:**
- **ML reranking models (rerankers, RankLLM)**: Designed for NLP/RAG document reranking. Wrong tool for weighted feature scoring in recommendation systems.
- **Collaborative filtering libraries**: Require critical mass of users. Content-based only for MVP (per PROJECT.md).
- **Qdrant `recommend()` API**: While available in v1.7.4, it's designed for positive/negative example recommendation, not multi-factor scoring. Use `search()` with user vector instead.
</sota_updates>

<open_questions>
## Open Questions

1. **Feed batch size vs freshness tradeoff**
   - What we know: Caching 60-item batches reduces Qdrant load, but cached items may become stale (already swiped elsewhere)
   - What's unclear: Optimal batch size and TTL for 300-500 product catalog with active users
   - Recommendation: Start with 60 items / 5-minute TTL. Monitor cache hit rate and stale-item rate. Adjust in Phase 12.

2. **Minimum cosine similarity threshold**
   - What we know: `score_threshold=0.2` is a conservative floor. Too high = empty feeds, too low = irrelevant items.
   - What's unclear: What threshold produces good recommendations for this specific embedding space (FashionSigLIP 768-dim)
   - Recommendation: Start at 0.2, log score distributions, tune based on user engagement data in Phase 11.

3. **Warm-start transition smoothness**
   - What we know: Users go from cold-start (cluster-based) to warm-start (user-vector-based) after onboarding
   - What's unclear: Whether the transition produces a noticeable quality shift
   - Recommendation: Log both cold-start and warm-start scores for first 5 feeds after onboarding. Compare distributions.

4. **Seen items set size management**
   - What we know: With ~500 products, users could exhaust catalog. Redis Set TTL handles cleanup.
   - What's unclear: At what seen/total ratio the feed quality degrades noticeably
   - Recommendation: When seen items > 70% of catalog, reset seen set and allow revisits with "You might like this again" flag. Track in Phase 11.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- Qdrant v1.7.4 search API — verified against project's `docker-compose.yml` (image: `qdrant/qdrant:v1.7.4`) and `pyproject.toml` (`qdrant-client>=1.7,<1.13`)
- Qdrant filtering documentation — `has_id` must_not filter for seen-item exclusion, Range filter for price
- Existing codebase `cold_start_service.py` — diversity injection pattern (3/20 from adjacent clusters, interleaved)
- Existing codebase `user_vector.py` — user vector computation (Modified Rocchio), price profile (IQR-based)
- Existing codebase `qdrant.py` — collections structure (products, style_clusters, user_profiles), all 768-dim cosine

### Secondary (MEDIUM confidence)
- Qdrant 1.14 blog post — Score-Boosting Reranker details (verified, but not usable at v1.7.4)
- Qdrant hybrid queries documentation — Prefetch, RRF, DBSF fusion (verified, but requires v1.10+)
- Google ML recommendation re-ranking guide — Two-stage pipeline pattern (industry standard)
- Multi-stage recommender systems (Towards Data Science) — Candidate generation → scoring → re-ranking
- Score normalization techniques (OpenSearch, Medium) — Min-max scaling for combining heterogeneous scores

### Tertiary (LOW confidence - needs validation)
- Exponential decay half-life formula — Standard math, but 14-day half-life specific to PROJECT.md spec. Actual optimal decay rate TBD from user data.
- Gaussian price affinity in log-space — Sound mathematical approach, but specific σ parameter needs tuning with real price distributions.
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Qdrant v1.7.4 vector search + FastAPI + Redis
- Ecosystem: No new libraries needed — existing stack covers all requirements
- Patterns: Two-stage pipeline, pre-computed feed batches, diversity injection, cursor pagination
- Pitfalls: Score normalization, empty feeds, cache staleness, price filter aggressiveness

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies, verified existing stack capabilities
- Architecture: HIGH - two-stage pipeline is industry standard, cold_start_service.py proves the pattern
- Pitfalls: HIGH - well-documented in recommendation system literature, specific to our Qdrant version constraints
- Code examples: HIGH - based on existing codebase patterns and verified Qdrant v1.7.4 API

**Research date:** 2026-03-12
**Valid until:** 2026-04-12 (30 days — stack is stable, no version changes planned)
</metadata>

---

*Phase: 05-feed-generation-ranking*
*Research completed: 2026-03-12*
*Ready for planning: yes*
