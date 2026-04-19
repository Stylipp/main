# Phase 17: Scraper-to-Backend Hardening - Research

**Researched:** 2026-04-19
**Domain:** Batch sync contracts, product archival, stable ID extraction, Hebrew category normalization
**Confidence:** HIGH

<research_summary>
## Summary

Researched the patterns and approaches needed to harden the scraper-to-backend sync pipeline. Phase 17 covers six distinct concerns: (1) per-product sync result contracts, (2) selective hash updates, (3) failure retry, (4) product archival with Qdrant exclusion, (5) stable source IDs from e-commerce pages, and (6) Hebrew category normalization expansion.

The existing codebase already has strong foundations — SHA-256 change detection, JSON-LD + HTML extraction, and Hebrew category mapping with 60+ keywords. The gaps are well-scoped: the batch ingest response needs per-item IDs (not just counts), the scraper blindly updates all hashes regardless of backend acceptance, removed products are deleted from SQLite but never archived in PostgreSQL/Qdrant, and `external_id` is always `md5(url)[:16]` even when pages expose stable product IDs.

**Primary recommendation:** Use HTTP 207 Multi-Status with per-item `accepted_ids`/`rejected` arrays. For archival, use soft-delete (`archived_at` column) in PostgreSQL + Qdrant payload filter (not point deletion) to preserve interaction history. Extract stable IDs from JSON-LD `sku` field and WooCommerce `data-product_id` HTML attribute, falling back to `md5(url)[:16]`.
</research_summary>

<standard_stack>
## Standard Stack

No new libraries needed. Phase 17 uses the existing stack:

### Core (Already Installed)
| Library | Purpose | Phase 17 Usage |
|---------|---------|----------------|
| httpx | Async HTTP client | Scraper-to-backend API calls (already used) |
| aiosqlite | Async SQLite | Change detection state (already used) |
| qdrant-client | Vector DB client | Point payload updates + filtered search (already used) |
| SQLAlchemy | ORM | Product model soft-delete column (already used) |
| Alembic | Migrations | Add `archived_at` column (already used) |
| BeautifulSoup | HTML parsing | Stable ID extraction from `data-product_id` (already used) |

### No New Dependencies
Phase 17 is pure logic hardening — no new libraries, no new infrastructure. All changes are to existing modules.
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Per-Item Batch Response Contract (HTTP 207)

**What:** Replace aggregate counts with per-item success/failure tracking in batch ingest response.
**When to use:** Any batch API where the client needs to know which specific items succeeded or failed.

**Current response:**
```python
# BatchIngestResponse (current)
class BatchIngestResponse(BaseModel):
    total: int
    created: int
    updated: int
    failed: int
    errors: list[dict]  # {external_id, store_id, error}
```

**Recommended response:**
```python
# BatchIngestResponse (hardened)
class BatchIngestResponse(BaseModel):
    total: int
    created: int
    updated: int
    failed: int
    accepted_ids: list[str]      # external_ids that succeeded
    rejected: list[RejectedItem] # external_ids that failed + reason

class RejectedItem(BaseModel):
    external_id: str
    store_id: str
    error: str
    retryable: bool  # True = transient (network, timeout), False = permanent (validation)
```

**HTTP status codes:**
- `200` — all items succeeded
- `207` — partial success (some accepted, some rejected)
- `400` — all items failed validation
- `500` — server error (all retryable)

**Why 207:** RFC 4918 Multi-Status is the standard for batch operations with mixed results. Clients can distinguish "retry these 3" from "fix these 2 and retry."

**Source:** [REST Bulk API Partial Success (2026)](https://oneuptime.com/blog/post/2026-02-02-rest-bulk-api-partial-success/view), [Adidas API Guidelines](https://adidas.gitbook.io/api-guidelines/rest-api-guidelines/execution/batch-operations)

### Pattern 2: Soft-Delete with Qdrant Payload Filter

**What:** Archive products by setting `archived_at` in PostgreSQL and adding `archived: true` to Qdrant payload, then filter in search queries. Do NOT hard-delete Qdrant points.
**When to use:** When user interaction history references the product and deletion would orphan records.

**Why not hard-delete Qdrant points:**
1. User interactions reference product IDs — orphaned foreign keys
2. Collections/saves would lose their items
3. Re-listing a product requires full re-embedding (expensive)
4. Filter-based deletion at scale can cause high server load and OOM ([qdrant/qdrant#6401](https://github.com/qdrant/qdrant/issues/6401))

**Implementation:**
```python
# PostgreSQL: Add archived_at column to Product model
archived_at: Mapped[Optional[datetime]] = mapped_column(nullable=True, default=None)

# Qdrant: Set payload flag on archived products
await qdrant.set_payload(
    collection_name="products",
    payload={"archived": True},
    points=[str(product.id)],
)

# Feed service: Add filter to exclude archived products
filter.must_not.append(
    FieldCondition(key="archived", match=MatchValue(value=True))
)
```

**Important:** Create a Qdrant payload index on the `archived` field for filter performance:
```python
await qdrant.create_payload_index(
    collection_name="products",
    field_name="archived",
    field_schema=PayloadSchemaType.BOOL,
)
```

**Source:** [Qdrant Payload Docs](https://qdrant.tech/documentation/manage-data/payload/), [Qdrant Delete Points API](https://api.qdrant.tech/api-reference/points/delete-points)

### Pattern 3: Selective Hash Update After Partial Success

**What:** Only update SQLite hashes for products in `accepted_ids`, not for rejected ones.
**When to use:** When the sync target (backend) can partially fail and the client needs retry semantics.

**Current flow (broken):**
```
scraper → push_products(new) → update_hashes(ALL new)  # BUG: includes failed
```

**Correct flow:**
```
scraper → push_products(new) → response.accepted_ids
        → update_hashes(ONLY products where external_id in accepted_ids)
        # Rejected products keep old/no hash → retried on next run
```

**Why this works:** A product with no hash in SQLite appears as "new" on the next `detect_changes()` call. A product with a stale hash appears as "changed." Either way, it gets re-sent to the backend — automatic retry with zero extra logic.

### Pattern 4: Stable Source ID Extraction

**What:** Extract the platform's native product ID from page HTML/JSON-LD instead of always using `md5(url)[:16]`.
**When to use:** When the source platform has stable IDs that survive URL changes.

**WooCommerce ID sources (priority order):**
1. **JSON-LD `sku` field** — `{"@type": "Product", "sku": "wp-pennant"}` (HIGH reliability)
2. **HTML `data-product_id` attribute** — `<div data-product_id="123">` (HIGH reliability, WooCommerce-specific)
3. **Body class `postid-{N}`** — `<body class="... postid-123 ...">` (MEDIUM reliability, WordPress convention)
4. **URL path segment** — `/product/blue-sneakers/` → slug extraction (LOW reliability, changes on rename)

**Shopify ID sources (priority order):**
1. **JSON-LD `productGroupID`** — `{"productGroupID": "7890123456"}` (HIGH reliability)
2. **JSON-LD `sku`** — variant-level SKU (HIGH reliability)
3. **Meta tag** — `<meta property="og:product:id" content="...">` (MEDIUM reliability)

**Recommended extraction function:**
```python
def extract_stable_id(soup: BeautifulSoup, jsonld: dict | None, platform: str) -> str | None:
    """Try to extract a stable product ID. Returns None if no reliable source found."""
    # 1. JSON-LD sku (all platforms)
    if jsonld and jsonld.get("sku"):
        return str(jsonld["sku"]).strip()

    # 2. Platform-specific HTML
    if platform == "woocommerce":
        el = soup.find(attrs={"data-product_id": True})
        if el:
            return el["data-product_id"]
        # Body class fallback
        body = soup.find("body")
        if body:
            for cls in body.get("class", []):
                if cls.startswith("postid-"):
                    return cls.replace("postid-", "")

    elif platform == "shopify":
        if jsonld and jsonld.get("productGroupID"):
            return str(jsonld["productGroupID"])

    return None  # caller falls back to md5(url)[:16]
```

**Key decision:** `external_id` format becomes `{platform}_{stable_id}` (e.g., `woo_123`, `shopify_7890123456`) when a stable ID is found, and `md5_{hash16}` when falling back. The prefix prevents cross-platform collisions.

**Source:** [WooCommerce Structured Data Wiki](https://github.com/woocommerce/woocommerce/wiki/Structured-data-for-products), [Shopify JSON-LD Templates](https://www.netprofitmarketing.com/product-schema-on-shopify-json-ld-templates-that-scale/)

### Anti-Patterns to Avoid
- **Hard-deleting Qdrant points for archival:** Breaks interaction history, expensive to reverse if product re-appears
- **Updating all hashes after partial sync:** Silently drops failed products — they'll never be retried
- **Using URL as identity:** URLs change on title renames, slug updates, or domain migrations
- **Transactional batch semantics (all-or-nothing):** One bad image shouldn't block 49 good products
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Unicode normalization for Hebrew | Custom regex/char mapping | Python `unicodedata.normalize('NFC', text)` | Hebrew has multiple Unicode representations (geresh, apostrophe variants); NFC canonical form handles this |
| Product ID from JSON-LD | Manual JSON parsing per platform | Existing `_find_product_node()` + `.get("sku")` | JSON-LD Product schema is standardized; `sku` field is cross-platform |
| Retry queue for failed products | Redis queue or separate job system | SQLite hash absence = automatic retry | Products without updated hashes re-appear as "new" or "changed" on next run — retry is implicit |
| Qdrant bulk archival | Loop of individual `set_payload` calls | `set_payload` with filter on `store_id` | Qdrant supports filter-targeted payload updates in a single call |
| HTTP 207 response parsing | Custom status code handling | Check `response.status_code in (200, 207)` and parse `accepted_ids` | 207 is standard; same JSON body structure for both 200 and 207 |

**Key insight:** The retry mechanism is already built into the change detection architecture. A product that fails backend ingestion simply doesn't get its hash updated in SQLite. On the next scraper run, `detect_changes()` sees it as new/changed and re-sends it. Zero additional infrastructure needed — just stop updating hashes for failed products.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Hebrew Geresh/Apostrophe Variants
**What goes wrong:** Hebrew words with geresh (׳) like ג׳ינס don't match because the category mapping uses ASCII apostrophe (') while the scraped text uses Hebrew geresh (׳) or Unicode modifier letter apostrophe (ʼ).
**Why it happens:** Hebrew has 3+ visually identical "apostrophe" characters: U+0027 (ASCII), U+05F3 (Hebrew geresh ׳), U+2019 (right single quote).
**How to avoid:** Normalize all apostrophe-like characters to ASCII `'` before token matching. The current code already has both `ג'ינס` and `ג׳ינס` in the keyword set, but new Hebrew terms must include all variants.
**Warning signs:** Products with ג׳קט, ז׳קט, or קפוצ׳ון in categories landing in "other."

### Pitfall 2: Archival Race Condition with Re-Listed Products
**What goes wrong:** A product is archived on run N (removed from sitemap), but re-appears on run N+1 (store re-listed it). If the scraper creates a new product instead of un-archiving, you get duplicates.
**Why it happens:** The scraper uses `external_id` as the dedup key, but if the URL changed, `md5(url)` produces a different external_id for the same real product.
**How to avoid:** Stable source IDs (Pattern 4) prevent this. Additionally, the backend ingest endpoint should check for archived products with the same `external_id` and un-archive them instead of creating new ones.
**Warning signs:** Product count growing faster than expected; duplicate-looking items in feed.

### Pitfall 3: Qdrant Payload Index Missing
**What goes wrong:** Feed queries become slow after adding `archived` filter because Qdrant does a full scan instead of using an index.
**Why it happens:** Qdrant doesn't auto-create payload indexes. Without `create_payload_index(field_name="archived")`, every search scans all points.
**How to avoid:** Create the payload index in a startup migration or one-time script before deploying archival.
**Warning signs:** Feed response times spike after archival feature ships.

### Pitfall 4: Scraper Updates Hashes Before Knowing Backend Result
**What goes wrong:** `update_hashes()` is called for all synced products, but `push_products()` returns only a count, not which specific products succeeded.
**Why it happens:** Current `BackendSync.push_products()` returns `int` (count created), not a list of accepted external_ids. The pipeline calls `update_hashes(report.new + report.changed)` unconditionally.
**How to avoid:** Change `push_products()` to return `list[str]` (accepted external_ids). Only pass those to `update_hashes()`.
**Warning signs:** Products that fail backend ingestion (bad image, quality gate rejection) never appear again because their hash is already in SQLite.

### Pitfall 5: `mark_removed()` Hard-Deletes from SQLite
**What goes wrong:** When a product is removed from the sitemap, `mark_removed()` DELETEs the row from SQLite. If the product later re-appears in the sitemap, the scraper treats it as brand new and re-ingests it — potentially creating a duplicate in PostgreSQL if the URL (and thus md5 external_id) changed.
**Why it happens:** Current `mark_removed()` uses `DELETE FROM product_hashes` instead of soft-delete.
**How to avoid:** Change `mark_removed()` to set a `removed_at` timestamp instead of deleting. On re-appearance, clear `removed_at`.
**Warning signs:** Product counts in SQLite shrink after every run; re-listed products create duplicates.
</common_pitfalls>

<code_examples>
## Code Examples

### Batch Ingest Response with Per-Item IDs
```python
# Source: Existing router.py pattern, extended with accepted_ids
# apps/backend/src/features/products/router/router.py

@router.post("/ingest/batch", response_model=BatchIngestResponse)
async def batch_ingest(request: BatchIngestRequest, ...):
    accepted_ids: list[str] = []
    rejected: list[dict] = []

    for product_data in request.products:
        try:
            await ingestion_service.ingest_or_update_product(product_data, session)
            accepted_ids.append(product_data.external_id)
        except Exception as e:
            rejected.append({
                "external_id": product_data.external_id,
                "store_id": product_data.store_id,
                "error": str(e),
                "retryable": not isinstance(e, ValidationError),
            })

    status_code = 200 if not rejected else 207
    return JSONResponse(
        status_code=status_code,
        content=BatchIngestResponse(
            total=len(request.products),
            created=...,
            updated=...,
            failed=len(rejected),
            accepted_ids=accepted_ids,
            rejected=rejected,
        ).model_dump(),
    )
```

### Selective Hash Update in Scraper
```python
# Source: Existing pipeline.py pattern, modified for selective updates
# apps/scraper/scraper/pipeline.py

# After sync:
if report.new:
    result = await sync.push_products(report.new)
    # Only update hashes for accepted products
    accepted_new = [p for p in report.new if p.external_id in result.accepted_ids]
    if accepted_new:
        await detector.update_hashes(store.id, accepted_new)

if report.changed:
    result = await sync.update_products(report.changed)
    accepted_changed = [p for p in report.changed if p.external_id in result.accepted_ids]
    if accepted_changed:
        await detector.update_hashes(store.id, accepted_changed)
```

### Product Archival in Backend
```python
# Source: Qdrant set_payload API docs
# apps/backend/src/features/products/service/ingestion_service.py

async def archive_products(self, external_ids: list[str], store_id: str):
    """Archive products removed from source sitemap."""
    # 1. Soft-delete in PostgreSQL
    stmt = (
        update(Product)
        .where(Product.external_id.in_(external_ids), Product.store_id == store_id)
        .values(archived_at=datetime.utcnow())
        .returning(Product.id)
    )
    result = await session.execute(stmt)
    archived_pg_ids = [str(row.id) for row in result]

    # 2. Mark archived in Qdrant payload
    if archived_pg_ids:
        await qdrant.set_payload(
            collection_name="products",
            payload={"archived": True},
            points=archived_pg_ids,
        )

    return archived_pg_ids
```

### Stable ID Extraction
```python
# Source: WooCommerce structured data wiki + Shopify docs
# apps/scraper/scraper/product_scraper.py

def _extract_stable_id(
    soup: BeautifulSoup, jsonld_node: dict | None, platform: str
) -> str | None:
    """Extract platform-native product ID. Returns None to fall back to md5(url)."""
    # JSON-LD sku (cross-platform)
    if jsonld_node:
        sku = jsonld_node.get("sku")
        if sku and str(sku).strip():
            return str(sku).strip()

    # WooCommerce: data-product_id attribute
    if platform == "woocommerce":
        el = soup.find(attrs={"data-product_id": True})
        if el and el.get("data-product_id", "").strip():
            return el["data-product_id"].strip()

    # Shopify: productGroupID in JSON-LD
    if platform == "shopify" and jsonld_node:
        group_id = jsonld_node.get("productGroupID")
        if group_id:
            return str(group_id).strip()

    return None

# Usage in scrape_product():
stable_id = _extract_stable_id(soup, jsonld_data, store.platform)
if stable_id:
    external_id = f"{store.platform}_{stable_id}"
else:
    external_id = f"md5_{hashlib.md5(url.encode()).hexdigest()[:16]}"
```

### Hebrew Apostrophe Normalization
```python
# Source: Unicode standard, Hebrew typography conventions
# apps/backend/src/features/products/utils/category.py

import unicodedata

def _normalize_category_value(value: str) -> str:
    decoded = unquote_plus(str(value)).strip().lower()
    # Normalize Unicode (NFC form)
    decoded = unicodedata.normalize("NFC", decoded)
    # Normalize apostrophe variants to ASCII
    decoded = decoded.replace("\u05F3", "'")  # Hebrew geresh ׳
    decoded = decoded.replace("\u2019", "'")  # Right single quote '
    decoded = decoded.replace("\u02BC", "'")  # Modifier letter apostrophe ʼ
    decoded = decoded.replace("\u2018", "'")  # Left single quote '
    return re.sub(r"\s+", " ", decoded)
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Aggregate batch counts | Per-item accepted/rejected IDs | Industry standard (RFC 4918) | Enables selective retry without full re-sync |
| Hard-delete from vector DB | Soft-delete via payload filter | Qdrant best practice | Preserves data for analytics, avoids OOM on bulk deletes |
| URL-based product identity | JSON-LD sku / platform native ID | Always preferred | Products survive URL renames, slug changes |

**Qdrant notes:**
- Filter-based bulk deletion can cause OOM on large collections ([qdrant/qdrant#6401](https://github.com/qdrant/qdrant/issues/6401)) — payload-flag soft-delete is safer
- `set_payload` with filter support makes bulk archival efficient
- Payload indexes (`create_payload_index`) are critical for filter performance on boolean fields

**No deprecated patterns** — the existing stack (httpx, aiosqlite, qdrant-client, SQLAlchemy) is current and stable.
</sota_updates>

<open_questions>
## Open Questions

1. **Should `external_id` format change be backward-compatible?**
   - What we know: Existing products use `md5(url)[:16]` format. New format would be `{platform}_{stable_id}` or `md5_{hash16}`.
   - What's unclear: Whether to migrate existing external_ids or grandfather them.
   - Recommendation: Grandfather existing IDs. New products get the new format. The backend already deduplicates on `(store_id, external_id)` — no collision risk since the format prefix differs.

2. **Should archival trigger Qdrant point deletion eventually?**
   - What we know: Soft-delete preserves interaction history and is cheaper. But archived points still consume storage and memory.
   - What's unclear: At what scale (10K? 100K? products) the storage cost matters.
   - Recommendation: Start with soft-delete only. Add a periodic cleanup job that hard-deletes points archived for >90 days if storage becomes a concern. Not needed for MVP scale (<10K products).

3. **How should the scraper notify the backend about removed products?**
   - What we know: The scraper detects `removed_ids` (external_ids no longer in sitemap). Currently it only deletes from SQLite.
   - What's unclear: Whether to add a new backend endpoint (`POST /api/products/archive/batch`) or extend the existing ingest endpoint.
   - Recommendation: New endpoint `POST /api/products/archive/batch` with body `{store_id, external_ids: [...]}`. Simpler than overloading the ingest endpoint with removal semantics.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- [Qdrant Delete Points API](https://api.qdrant.tech/api-reference/points/delete-points) — deletion by ID and filter, Python client examples
- [Qdrant Payload Documentation](https://qdrant.tech/documentation/manage-data/payload/) — set_payload, payload indexes, filter performance
- [WooCommerce Structured Data Wiki](https://github.com/woocommerce/woocommerce/wiki/Structured-data-for-products) — JSON-LD output with `sku` field, `@id` format
- Codebase analysis: `apps/scraper/`, `apps/backend/src/features/products/` — verified current architecture

### Secondary (MEDIUM confidence)
- [REST Bulk API Partial Success (2026)](https://oneuptime.com/blog/post/2026-02-02-rest-bulk-api-partial-success/view) — HTTP 207 pattern, response structure, verified against RFC 4918
- [Adidas API Guidelines - Batch Operations](https://adidas.gitbook.io/api-guidelines/rest-api-guidelines/execution/batch-operations) — industry standard batch patterns
- [Shopify JSON-LD Templates](https://www.netprofitmarketing.com/product-schema-on-shopify-json-ld-templates-that-scale/) — `productGroupID` field, variant SKU handling
- [Qdrant Issue #6401](https://github.com/qdrant/qdrant/issues/6401) — filter-based bulk deletion causing OOM, confirms soft-delete preference

### Tertiary (LOW confidence - needs validation during implementation)
- WooCommerce `data-product_id` HTML attribute — confirmed exists in standard themes, but may vary with custom themes. Validate against actual target stores during implementation.
- Hebrew fashion vocabulary coverage — compared existing 60+ keywords against linguistic references. Some niche terms (בגד ים/swimwear, ספורט/sportswear) may be missing but are edge cases.
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Qdrant payload operations, PostgreSQL soft-delete
- Ecosystem: WooCommerce/Shopify structured data, JSON-LD Product schema
- Patterns: HTTP 207 batch responses, selective retry, soft-delete vs hard-delete
- Pitfalls: Hebrew Unicode normalization, hash update race conditions, Qdrant indexing

**Confidence breakdown:**
- Batch sync contract: HIGH — well-documented REST pattern (RFC 4918), verified with multiple sources
- Product archival: HIGH — Qdrant payload filter is documented and proven; soft-delete is standard
- Stable source IDs: MEDIUM — JSON-LD `sku` is reliable, but `data-product_id` availability varies by theme
- Hebrew normalization: HIGH — existing mapping is solid; gap is apostrophe variant handling, not missing vocabulary
- Code examples: HIGH — derived from existing codebase patterns + verified Qdrant/WooCommerce docs

**Research date:** 2026-04-19
**Valid until:** 2026-05-19 (30 days — all technologies stable, no breaking changes expected)
</metadata>

---

*Phase: 17-scraper-hardening*
*Research completed: 2026-04-19*
*Ready for planning: yes*
