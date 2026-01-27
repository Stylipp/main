# AI Personal Stylist

## What This Is

An AI-powered fashion discovery app that provides high-quality, personalized clothing recommendations from the first session. Users upload 2 outfit photos, complete 15 calibration swipes, and receive a continuously-learning feed of products matched to their style. Built as a Progressive Web App with affiliate revenue model, targeting English-speaking fashion consumers who want effortless style discovery without the work of traditional search.

## Core Value

**Users get relevant fashion recommendations immediately—no lengthy questionnaires, no 50-swipe training period, no guessing what to search for.** The cluster-based cold-start system ensures even brand-new users see contextually appropriate items from their first interaction. If this doesn't work, nothing else matters.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] **Cluster-based cold-start system**: Pre-cluster entire product catalog (200-500 style clusters using FashionSigLIP embeddings). New users instantly see products from their nearest clusters based on 2 uploaded photos.
- [ ] **Minimal onboarding**: 2 outfit photos + 15 calibration swipes to personalized feed. Time-to-value under 3 minutes.
- [ ] **Silent continuous learning**: System learns from every swipe, save, click, and view time without explicit user feedback requests. Weighted vector formula: `user_vector = 1.0 * positive_centroid - 0.7 * negative_centroid` with 14-day time decay.
- [ ] **Multi-factor feed ranking**: Cosine similarity (65%), cluster prior (15%), price affinity (10%), freshness (10%) with mandatory diversity injection (3/20 items from adjacent clusters).
- [ ] **Image quality gate**: Block blurry, too-small, or low-quality uploads that would pollute style vectors. Validate dimensions (400px min), file size (50KB-10MB), and blur detection via Laplacian variance.
- [ ] **Price sensitivity profiling**: Track preferred min/max, median clicked price, median saved price. Nightly batch updates. Use in ranking to avoid showing unaffordable items.
- [ ] **Perceptual hash deduplication**: Prevent same product from multiple stores appearing repeatedly. Hamming distance threshold of 5 for duplicate detection.
- [ ] **Partner store ingestion**: WooCommerce API integration for product catalog. Bootstrap fallback store (300-500 curated products) to prevent Week 1 dependency block.
- [ ] **Affiliate tracking**: End-to-end click tracking with commission attribution. Every product click must be trackable to measure business model viability.
- [ ] **Style collections**: User-created folders for saved items ("Summer vacation," "Work outfits"). Increases engagement and emotional investment.
- [ ] **Simple explainability**: 3 template-based explanations only (no category labeling): "Similar to your recent likes," "Matches your style," "Within your usual price range."
- [ ] **Analytics from day one**: Full event taxonomy (feed views, swipes, clicks, onboarding steps) instrumented immediately. Track D7 retention, swipe-to-save ratio, affiliate CTR, onboarding completion.
- [ ] **GDPR decision logs**: Every recommendation decision logged with similarity score, cluster ID, price score, timestamp for audit trail and debugging.
- [ ] **PWA with offline capability**: Installable on iOS and Android home screens, works offline with cached content.
- [ ] **English primary, translation-ready**: All UI copy in English with architecture supporting future translation addition.

### Out of Scope

- **Face recognition** — Legal complexity (GDPR Article 9 biometric data), user trust barriers, and zero contribution to fashion preference understanding. Face tells you nothing about style.
- **Person detection (MVP)** — Adds 2-3 weeks of work. Users self-select relevant photos; FashionSigLIP handles full-frame clothing well enough for MVP. Add RT-DETR (Apache 2.0) in Phase 2 only if embedding quality degrades.
- **Search functionality** — Requires comprehensive product tagging, synonym handling, spelling correction, and relevance ranking. 4-6 week project. Discovery via swipe is the MVP value prop. Add in Phase 2 with robust metadata.
- **Native mobile apps** — Three codebases (iOS, Android, backend) vs. one PWA. App Store review delays block rapid iteration. No push notifications on iOS acceptable for MVP.
- **Social features** — No sharing, following, public profiles, or social feed. Pure personal discovery tool.
- **User-generated content** — Users cannot upload products or create public collections. Curated partner inventory only.
- **Advanced filtering** — No manual price/category/style filters. Pure algorithmic feed. Filters imply search, which is out of scope.
- **Collaborative filtering** — "Users like you also liked..." requires critical mass of users. Content-based only for MVP.
- **Category-based explanations** — "Similar to your saved sneakers" requires product taxonomy that doesn't exist yet. Too complex for MVP.

## Context

### Market Opportunity
Fashion e-commerce users struggle with:
- **Search requires knowing what you want** — Most users browse because they can't articulate their style preferences
- **Traditional discovery is time-consuming** — Browsing stores manually takes hours
- **Generic recommendations miss the mark** — "Popular items" don't match individual taste

This creates an opening for AI-powered personal discovery that combines the ease of swiping with recommendation quality that feels intelligent from the first interaction.

### Technical Innovation
The cluster-based cold-start approach solves the fundamental recommendation system chicken-and-egg problem without forcing users through lengthy questionnaires. By pre-computing style clusters and instantly matching users to relevant segments, we deliver perceived intelligence before any personal learning occurs. This is the core technical insight that enables the MVP timeline.

### Architecture Philosophy
- **Synchronous inference for MVP**: No premature async complexity. Semaphore-limited (4 concurrent) CPU inference handles <200 users comfortably.
- **Single source of truth per data type**: Product embeddings in Qdrant only (not duplicated in PostgreSQL). Prevents sync bugs and saves 40% storage cost.
- **Add infrastructure in response to measurement**: ARQ task queue, GPU nodes, and auto-scaling deferred until metrics (p95 latency >500ms, concurrent users >200) justify the complexity.

### Open Source AI Models (License Safety)
All models Apache 2.0 or MIT licensed. Explicit AGPL avoidance (YOLOv8 excluded) to eliminate copyleft risk for proprietary SaaS:
- **Marqo-FashionSigLIP** (Apache 2.0): Style embeddings
- **RT-DETR** (Apache 2.0): Person detection (Phase 2 if needed)
- **SAM** (Apache 2.0): Segmentation (Phase 2)

## Constraints

- **Timeline**: 6 weeks hard deadline to MVP launch with 50-100 user soft launch
- **Team**: Solo developer — all architecture decisions optimized for single-person velocity
- **Language**: English primary, with architecture supporting future translation addition (no Hebrew requirement for MVP)
- **Infrastructure Budget**: Optimize for early-stage cost control. No Kubernetes, no GPU clusters, no enterprise services until growth justifies it.
- **Legal Compliance**: GDPR-compliant from day one (decision logs, right to erasure, data retention policies)
- **License Safety**: All AI models must be Apache 2.0, MIT, or similarly permissive. No AGPL or restrictive licenses that create SaaS legal risk.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Vite + React + MUI (not Next.js) | Fastest HMR, MUI provides production-ready components with accessibility, no SSR complexity needed for PWA | — Pending |
| FastAPI backend (not Django/Flask) | Native async support, automatic OpenAPI docs, Pydantic validation, excellent ML ecosystem integration | — Pending |
| Qdrant for vectors (not Pinecone) | Self-hosted option for cost control, excellent filtering capabilities, no vendor lock-in | — Pending |
| Custom swipe component (not react-tinder-card) | Full control over gesture physics, no dependency on abandoned library, tailored UX | — Pending |
| Remove face recognition entirely | Cuts 30% of complexity, eliminates GDPR Article 9 biometric data burden, provides zero value for fashion preference understanding | — Pending |
| Cluster-based cold start | Enables immediate relevance without 50-swipe training. Differentiator from competitors using questionnaires or random exploration | — Pending |
| 2 photos + 15 swipes onboarding | Balances learning data with friction. Under 3 minutes time-to-value vs. 5-8 minutes in original plan | — Pending |
| Synchronous inference for MVP | Eliminates queue/worker complexity, <1s latency acceptable with semaphore limiting, easier debugging | — Pending |
| Bootstrap store fallback | Prevents Week 1 partner dependency block. 300-500 curated products enable parallel development | — Pending |
| Diversity injection mandatory | Prevents echo chamber effect. Force 3/20 items from adjacent clusters maintains discovery while preserving relevance | — Pending |
| Analytics from day one | Not retrofittable. Need data immediately to debug cold start, validate ranking weights, identify drop-off points | — Pending |
| Template-only explainability | Category-based explanations require taxonomy that doesn't exist. 3 simple templates ship in MVP, semantic explanations deferred to Phase 2 | — Pending |

## Technology Stack (MVP)

### Frontend
- React 18 + TypeScript (Vite)
- MUI v5 for UI
- Zustand for client state
- TanStack Query for server state
- React Router v6
- Axios
- React Hook Form + Zod
- Custom swipe component (framer-motion)
- vite-plugin-pwa

### Backend
- FastAPI (Python 3.12+)
- SQLAlchemy 2.0 (async) + Alembic
- Pydantic v2
- PostgreSQL (pgvector installed; minimal MVP use)
- Qdrant for product embeddings
- Redis (cache only)
- JWT auth (python-jose)
- Hetzner Object Storage (S3-compatible)

## Monorepo & Architecture

### Monorepo Structure (pnpm workspaces)
- `apps/web` (PWA)
- `apps/backend` (FastAPI)
- `packages/shared` (types/constants)
- `infra` (docker compose, tunnel config)
- `.github/workflows` (CI)

### Backend Separation Rules
- `router.py`: HTTP only
- `service.py`: business logic only
- `repository.py`: DB/Qdrant only
- `schemas.py`: validation only
- `utils.py`: pure functions only

### Backend Feature Folder Convention
- Each feature uses subfolders with files inside, e.g. `ai/router/router.py` (not `ai/router.py`)

## Infrastructure & Ops

- Docker + Docker Compose (dev + prod)
- Traefik reverse proxy
- Cloudflare Tunnel
- GitHub Actions CI/CD
- Husky + lint-staged

## Analytics (From Day One)

- Event taxonomy: feed views, swipes, clicks, onboarding steps
- Store events in DB with session_id + user_id + timestamp + payload
- Track D1/D7 retention, swipe-to-save ratio, affiliate CTR, onboarding completion

## Execution Roadmap (6 Weeks)

- Week 1: Product ingestion + embeddings + clustering
- Week 2: Feed API + ranking logic
- Week 3: Swipe UI + feedback pipeline
- Week 4: Affiliate tracking end-to-end
- Week 5: Dedup + caching + monitoring
- Week 6: UX polish + soft launch (50-100 users)

## Risks & Mitigations

- Partner onboarding delays → bootstrap store fallback
- Model quality variance → image quality gate, Phase 2 detection if needed
- Tight testing window → prioritize critical path + load test before launch

## MVP Launch Checklist (Minimum)

- [ ] Bootstrap store populated (300+ products)
- [ ] Image quality gate tested with edge cases
- [ ] Analytics events flowing to DB
- [ ] Diversity injection verified
- [ ] Affiliate links track end-to-end
- [ ] Decision logs captured for every recommendation
- [ ] PWA installable on iOS and Android

---
*Last updated: 2026-01-27 after initialization*
