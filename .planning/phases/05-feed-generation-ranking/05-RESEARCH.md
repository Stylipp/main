# Phase 5: Feed Generation & Ranking - Research

**Researched:** 2026-03-12
**Domain:** Multi-factor recommendation ranking with Qdrant vector search
**Confidence:** HIGH

<research_summary>
## Summary

Researched the architecture and implementation patterns for building a multi-factor feed ranking system on top of Qdrant v1.7.4 with FastAPI. The system must combine cosine similarity (65%), cluster prior (15%), price affinity (10%), and freshness (10%) into a unified score, with mandatory diversity injection (3/20 items from adjacent clusters).

**Critical finding:** Qdrant v1.7.4 does not support the newer Query API, server-side score boosting, or fusion methods introduced in later releases. Multi-factor ranking must happen application-side in Python after candidate retrieval from Qdrant. This is the standard two-stage recommendation pattern: candidate generation -> application-side re-ranking.

The existing cold-start service already proves the diversity-injection pattern and the repo already computes a user vector plus price profile during onboarding. Phase 5 should build on those primitives rather than inventing a separate recommendation path.

**Primary recommendation:** Implement a two-stage feed pipeline. Qdrant retrieves about 100 candidates via user-vector cosine search with lightweight filtering, then Python re-ranks those candidates with weighted multi-factor scoring and diversity injection.

**Minimal Phase 5 deliverable:** Ship `GET /api/feed` that returns 20 ranked items for an onboarded user using the stored user vector, application-side scoring, and basic seen-item exclusion. Keep pagination simple at first. Redis feed-batch caching is optional and can be deferred unless latency proves problematic.

**Repo-specific constraint:** This repo already has a real Qdrant client/server compatibility concern recorded in `STATE.md`, and recent debugging confirmed that newer `query_points` paths can fail against the deployed Qdrant 1.7 server. Phase 5 should use the server-compatible `search` path or a compatibility wrapper, and exact client/server versions should be pinned before relying on newer Qdrant APIs.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| qdrant-client | `>=1.7,<1.13` | Vector similarity search for candidates | Already in project, handles Stage 1 retrieval |
| numpy | Existing | Score normalization and vector operations | Already used for embeddings and user vectors |
| math / datetime | stdlib | Freshness decay and price scoring | No dependency needed |

### Optional
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `redis.asyncio` | Add explicitly if needed | Feed batch caching and seen-item tracking | Optional for initial Phase 5, useful if caching is pulled forward |
| `uuid` / `base64` / `json` | stdlib | Opaque cursor pagination | Use if cursor-based paging is added in first pass |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Application-side ranking | Qdrant score-boosting reranker | Requires newer Qdrant server |
| Application-side ranking | Qdrant Query API + fusion | Requires newer Qdrant server |
| Redis seen-items Set | Qdrant `has_id` filter only | Redis adds TTL and faster repeated set operations, but is not wired yet |
| Redis feed cache | PostgreSQL materialized view | Redis is better for short-lived feed batches, but this is probably Phase 12 work |
| ML reranking libraries | Custom weighted scoring | Overkill for this weighted recommendation problem |

**Repo reality:** Redis is configured in `apps/backend/.env.example`, but no Python Redis client is currently declared in `apps/backend/pyproject.toml`. If feed caching or Redis-backed seen-item tracking ships in Phase 5, add that dependency explicitly. If caching is deferred, Phase 5 can proceed with the existing Qdrant + numpy + FastAPI stack.
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```text
src/features/feed/
|-- router/
|   `-- router.py          # GET /api/feed endpoint
|-- service/
|   |-- feed_service.py    # Orchestrates retrieval + ranking
|   |-- ranking_service.py # Multi-factor scoring logic
|   `-- feed_cache.py      # Optional Redis cache / seen-items helper
|-- schemas/
|   `-- schemas.py         # FeedResponse, FeedItem, cursor payloads
`-- utils/
    `-- scoring.py         # Normalization and scoring helpers
```

### Pattern 1: Two-Stage Candidate Generation -> Re-Ranking
**What:** Retrieve broad candidates from Qdrant, then score and re-rank in application code.  
**When to use:** Always. This is the standard recommendation-system architecture for content-based ranking.  
**Why:** Vector search handles nearest-neighbor retrieval efficiently, while price, freshness, cluster prior, and business rules belong in application code.

```python
# Stage 1: Candidate generation
candidates = await qdrant_client.search(
    collection_name="products",
    query_vector=user_vector,
    query_filter=query_filter,
    limit=100,
    score_threshold=0.2,
)

# Stage 2: Application-side scoring
scored_items = []
for candidate in candidates:
    cosine_score = candidate.score
    prior_score = get_cluster_prior(candidate.payload["cluster_id"])
    price_score = compute_price_affinity(
        candidate.payload["price"],
        user_price_profile,
    )
    freshness_score = compute_freshness(candidate.payload["created_at"])

    final_score = (
        0.65 * cosine_score
        + 0.15 * prior_score
        + 0.10 * price_score
        + 0.10 * freshness_score
    )
    scored_items.append((candidate, final_score))

scored_items.sort(key=lambda item: item[1], reverse=True)
```

### Pattern 2: Optional Feed Batch Caching
**What:** Generate a larger feed batch, cache it briefly, paginate from cache.  
**When to use:** When measured feed latency or repeated page-fetch cost becomes a real bottleneck.  
**Why:** Avoids re-running expensive retrieval and re-ranking for every page request.

For this repo, treat this as an optimization pattern, not a prerequisite. Start with uncached feed generation for the first Phase 5 delivery unless measurement shows it is too slow.

```python
FEED_BATCH_SIZE = 60
FEED_CACHE_TTL = 300  # 5 minutes

async def get_feed(user_id: str, cursor: str | None = None) -> FeedResponse:
    cache_key = f"feed:{user_id}"

    if cursor:
        cached_batch = await redis.get(cache_key)
        if cached_batch:
            batch = deserialize(cached_batch)
            page = batch[offset : offset + PAGE_SIZE]
            return FeedResponse(items=page, next_cursor=next_cursor)

    candidates = await retrieve_candidates(user_id, limit=100)
    ranked = rank_candidates(candidates, user_profile)
    final_batch = inject_diversity(ranked, FEED_BATCH_SIZE)

    await redis.setex(cache_key, FEED_CACHE_TTL, serialize(final_batch))
    return FeedResponse(items=final_batch[:PAGE_SIZE], next_cursor=encode_cursor(PAGE_SIZE))
```

### Pattern 3: Diversity Injection by Slot Reservation
**What:** Reserve 3 out of 20 slots for adjacent-cluster items and interleave them.  
**When to use:** Every feed generation, per `PROJECT.md`.  
**Why:** Prevents echo chambers and preserves discovery.

```python
def inject_diversity(
    primary_items: list[FeedCandidate],
    diversity_items: list[FeedCandidate],
    target_count: int = 20,
) -> list[FeedCandidate]:
    if not diversity_items:
        return primary_items[:target_count]

    primary_target = max(0, target_count - min(3, len(diversity_items)))
    primary_slice = primary_items[:primary_target]
    diversity_slice = diversity_items[: target_count - len(primary_slice)]

    chunk_size = max(1, math.ceil(len(primary_slice) / max(1, len(diversity_slice))))
    merged: list[FeedCandidate] = []
    primary_index = 0
    diversity_index = 0

    while primary_index < len(primary_slice) or diversity_index < len(diversity_slice):
        next_primary = min(len(primary_slice), primary_index + chunk_size)
        merged.extend(primary_slice[primary_index:next_primary])
        primary_index = next_primary

        if diversity_index < len(diversity_slice):
            merged.append(diversity_slice[diversity_index])
            diversity_index += 1

    return merged[:target_count]
```

### Pattern 4: Narrow First, Broaden on Shortfall
**What:** Try the best candidate filter first, then progressively widen if too few items remain.  
**When to use:** Small catalog, young product inventory, or aggressive seen-item exclusion.  
**Why:** Prevents empty feeds and protects UX.

Example widening sequence:
1. Use user vector + generous price filter + unseen items
2. Drop price filter if candidate count is too low
3. Drop cluster preference if candidate count is still too low
4. Allow revisits only as a last resort

### Recommended First Implementation Order
1. `GET /api/feed`
2. Candidate retrieval from Qdrant using stored user vector
3. Application-side weighted scoring
4. Diversity injection
5. Basic pagination
6. Optional cache only if needed
</architecture_patterns>

<dont_hand_roll>
## Do Not Hand-Roll

| Problem | Do Not Build | Use Instead | Why |
|---------|--------------|-------------|-----|
| Vector nearest-neighbor search | Custom brute-force distance code | Qdrant `search()` with cosine | Qdrant already solves ANN retrieval efficiently |
| Score normalization | Custom utility package | Small local helper using numpy / simple math | Easy and transparent |
| Cursor encoding | Homegrown ad hoc string format | Base64-encoded JSON | Standard, opaque, easy to debug |
| Short-lived cache | In-process dictionary cache | Redis if caching is actually needed | Shared across workers, survives restarts |
| Seen-item exclusion | Complicated SQL joins in first pass | Qdrant filter or simple per-user store | Keep Phase 5 lean |

**Key insight:** The custom logic is the weighted ranking formula and diversity policy. Retrieval, filtering, and basic pagination should stay boring.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Score Scale Mismatch
**What goes wrong:** Cosine similarity dominates every other factor.  
**Why it happens:** Cluster prior, freshness, and price naturally live on different scales.  
**How to avoid:** Normalize all factors to `[0, 1]` within the candidate batch before applying weights.

### Pitfall 2: Empty or Tiny Feed
**What goes wrong:** Users run out of unseen items quickly in a 300-500 product catalog.  
**Why it happens:** Small catalog plus seen-item exclusion is unforgiving.  
**How to avoid:** Widen retrieval progressively instead of returning empty results.

### Pitfall 3: Cold-Start to Warm-Start Quality Drop
**What goes wrong:** The first warm feed feels worse than the onboarding calibration feed.  
**Why it happens:** Warm-start ranking uses different logic and thresholds than cold-start.  
**How to avoid:** Keep the diversity pattern consistent and compare score distributions across the first few post-onboarding feed loads.

### Pitfall 4: Over-Aggressive Price Filtering
**What goes wrong:** Good style matches disappear because they are slightly outside the learned range.  
**Why it happens:** Price is used as a hard gate too early.  
**How to avoid:** Use a generous price filter in candidate retrieval and let price affinity influence rank, not strict inclusion.

### Pitfall 5: Caching Too Early
**What goes wrong:** Phase 5 becomes a caching/invalidation project instead of a feed-quality project.  
**Why it happens:** Redis feels easy, but cache invalidation around swipes and seen-items is real complexity.  
**How to avoid:** Defer caching until feed generation is actually working and measured.

### Pitfall 6: Qdrant Client/Server Feature Drift
**What goes wrong:** The code uses a client method that maps to an endpoint unsupported by the deployed server.  
**Why it happens:** Client and server versions are not pinned tightly enough.  
**How to avoid:** Use the server-compatible `search` path and pin exact versions. Add at least one integration test against the real Qdrant container.
</common_pitfalls>

<code_examples>
## Code Examples

### Freshness Score
```python
import math
from datetime import datetime, timezone

FRESHNESS_LAMBDA = math.log(2) / 14  # 14-day half-life


def compute_freshness_score(created_at: datetime) -> float:
    now = datetime.now(timezone.utc)
    days_old = max((now - created_at).total_seconds() / 86400, 0)
    return math.exp(-FRESHNESS_LAMBDA * days_old)
```

### Price Affinity
```python
import math


def compute_price_affinity(
    product_price: float,
    price_median: float,
    price_std: float,
) -> float:
    if product_price <= 0 or price_median <= 0:
        return 0.5

    log_price = math.log(product_price)
    log_median = math.log(price_median)
    sigma = max(price_std, price_median * 0.3)
    log_sigma = max(math.log(sigma), 0.1)

    exponent = -((log_price - log_median) ** 2) / (2 * log_sigma**2)
    return math.exp(exponent)
```

### Score Normalization
```python
def normalize_scores(scores: list[float]) -> list[float]:
    if not scores:
        return []

    minimum = min(scores)
    maximum = max(scores)
    spread = maximum - minimum

    if spread < 1e-8:
        return [0.5] * len(scores)

    return [(score - minimum) / spread for score in scores]
```

### Candidate Retrieval with Legacy Search Compatibility
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
    must = []
    must_not = []

    if seen_ids:
        must_not.append(models.HasIdCondition(has_id=seen_ids))

    if price_min > 0 and price_max > 0:
        must.append(
            models.FieldCondition(
                key="price",
                range=models.Range(
                    gte=price_min * 0.5,
                    lte=price_max * 2.0,
                ),
            )
        )

    query_filter = models.Filter(must=must, must_not=must_not) if (must or must_not) else None

    return await qdrant_client.search(
        collection_name="products",
        query_vector=user_vector,
        query_filter=query_filter,
        limit=limit,
        score_threshold=0.2,
        with_payload=True,
        with_vectors=False,
    )
```

### Opaque Cursor
```python
import base64
import json


def encode_cursor(offset: int, batch_id: str) -> str:
    payload = json.dumps({"o": offset, "b": batch_id})
    return base64.urlsafe_b64encode(payload.encode()).decode()


def decode_cursor(cursor: str) -> tuple[int, str]:
    payload = base64.urlsafe_b64decode(cursor.encode()).decode()
    data = json.loads(payload)
    return data["o"], data["b"]
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Single-stage vector ranking | Two-stage retrieve + re-rank | Standard production architecture |
| Offset pagination | Cursor-based pagination | More stable for dynamic feeds |
| Server-side magic ranking | Transparent application-side scoring | Easier to debug and tune on older infrastructure |
| Heavy recommender stacks | Lean content-based ranking | Better fit for early-stage catalog and low user count |

**Useful upgrade path later:** If Qdrant is upgraded and version-pinned cleanly, newer query and server-side ranking features may become available. That is a later optimization, not a Phase 5 dependency.
</sota_updates>

<open_questions>
## Open Questions

1. **How strict should seen-item exclusion be in the first feed version?**
   - What we know: hard exclusion improves UX, but the catalog is small
   - What is unclear: whether strict exclusion will starve the feed too quickly
   - Recommendation: start with exclusion, log shortfall rate, widen if necessary

2. **What is the right cosine threshold for FashionSigLIP in this catalog?**
   - What we know: `0.2` is a conservative floor
   - What is unclear: actual score distribution for this specific catalog
   - Recommendation: start at `0.2`, log candidate counts and score ranges

3. **Should Phase 5 include caching?**
   - What we know: caching can help, but invalidation adds complexity
   - What is unclear: whether Phase 5 feed latency will justify it
   - Recommendation: do not make caching mandatory in the first Phase 5 plan

4. **How smooth is the cold-start to warm-start transition?**
   - What we know: users complete onboarding and then rely on the stored user vector
   - What is unclear: whether the first warm feed feels noticeably worse
   - Recommendation: instrument and compare the first few warm feeds after onboarding
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- Existing repo `cold_start_service.py` - current diversity injection and Qdrant compatibility constraints
- Existing repo `user_vector.py` - user vector computation and price profile logic
- Existing repo `qdrant.py` - collections and vector shape
- Existing repo `PROJECT.md` - ranking weights and diversity requirement
- Existing repo `ROADMAP.md` - Phase 5 scope and later-phase caching/performance separation
- Existing repo `STATE.md` - documented Qdrant client/server mismatch concern

### Secondary (MEDIUM confidence)
- Qdrant 1.7 search/filtering documentation
- General recommendation-system literature on candidate generation -> re-ranking
- Standard pagination and caching patterns used in feed systems

### Tertiary (LOW confidence, tune with real data)
- Exact cosine threshold for good FashionSigLIP retrieval in this catalog
- Exact price-affinity shape and sigma tuning
- Exact freshness half-life effect on engagement
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Qdrant v1.7.4 vector search + FastAPI
- Optional optimization: Redis caching + seen-item tracking
- Patterns: two-stage ranking, optional feed-batch caching, diversity injection, cursor pagination
- Main repo constraint: Qdrant client/server compatibility

**Confidence breakdown:**
- Standard stack: MEDIUM-HIGH - ranking path is clear, Redis is not wired yet
- Architecture: HIGH - two-stage pipeline is the right fit
- Pitfalls: HIGH - grounded in this repo's actual constraints
- Code examples: MEDIUM-HIGH - valid for the current stack, but must respect the compatibility layer

**Research date:** 2026-03-12
**Valid until:** 2026-04-12
</metadata>

---

*Phase: 05-feed-generation-ranking*
*Research completed: 2026-03-12*
*Ready for planning: yes*
