# Roadmap: Stylipp

## Overview

A 15-phase journey from zero to MVP launch, building an AI-powered fashion discovery PWA that delivers personalized clothing recommendations from the first session. The roadmap progresses from foundational infrastructure through ML clustering and cold-start systems, to a production-ready swipe-based discovery interface with affiliate tracking and analytics. Each phase delivers a coherent, verifiable capability on the path to a 6-week soft launch with 50-100 users.

## Domain Expertise

None

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation & Infrastructure** - Monorepo setup, Docker, databases, auth, backend structure, CI/CD + git hooks, Traefik + Cloudflare Tunnel baseline, object storage config, i18n scaffolding
- [ ] **Phase 2: Product Ingestion & Embeddings** - Bootstrap store, WooCommerce API, FashionSigLIP, image quality gate
- [ ] **Phase 3: Clustering & Cold Start System** - Pre-cluster catalog, cluster priors, nearest cluster matching
- [ ] **Phase 4: User Onboarding & Profiles** - Photo upload (2), calibration swipes (15), user profiles, price profiling
- [ ] **Phase 5: Feed Generation & Ranking** - Multi-factor ranking algorithm, diversity injection, feed API
- [ ] **Phase 6: Swipe Interface & Feedback** - Custom swipe component, gesture physics, feedback pipeline
- [ ] **Phase 7: Learning & Personalization** - User vector updates, weighted centroid, time decay, continuous learning
- [ ] **Phase 8: Collections & Saves** - User folders, save functionality, collection management UI
- [ ] **Phase 9: Affiliate Tracking** - End-to-end click tracking, commission attribution, partner management
- [ ] **Phase 10: Deduplication & Data Quality** - Perceptual hashing, Hamming distance, duplicate prevention
- [ ] **Phase 11: Analytics & Decision Logs** - Event taxonomy, GDPR logs, retention tracking, instrumentation
- [ ] **Phase 12: Performance & Caching** - Redis caching, rate limiting, query optimization, latency monitoring
- [ ] **Phase 13: PWA Implementation** - Service worker, offline capability, installability (iOS/Android)
- [ ] **Phase 14: Polish & Quality Assurance** - Explainability templates, UX refinements, load testing, edge cases
- [ ] **Phase 15: Launch Readiness** - Monitoring dashboards, alerts, launch checklist, soft launch prep

## Phase Details

### Phase 1: Foundation & Infrastructure
**Goal**: Establish monorepo structure, Docker environment, database infrastructure (PostgreSQL, Qdrant, Redis), JWT authentication, and basic FastAPI backend with feature folder convention (e.g., `src/features/ai/router/router.py`) and core layer (`src/core/*`), plus CI/CD + git hooks, Traefik + Cloudflare Tunnel baseline, object storage configuration, and i18n scaffolding (English primary, translation-ready)

**Depends on**: Nothing (first phase)

**Research**: Unlikely (established patterns with pnpm workspaces, Docker Compose, FastAPI async patterns)

**Plans**: Defined

Plans:
- [ ] Initialize monorepo with `apps/web`, `apps/backend`, `packages/shared`, `infra`, `.github/workflows`
- [ ] Set up pnpm workspaces and root scripts (dev/build/lint/test)
- [ ] Add Docker Compose stack (Postgres, Qdrant, Redis) with Cloudflare → Traefik routing
- [ ] Add backend skeleton with feature folder convention (`src/features/<feature>/router/router.py`, `service.py`, `repository.py`, `schemas.py`, `utils.py`)
- [ ] Add backend core layer (`src/core/config.py`, `src/core/database.py`, `src/core/dependencies.py`)
- [ ] Configure database layer (SQLAlchemy async + Alembic) and core settings
- [ ] Implement JWT auth scaffold and storage scaffold
- [ ] Set up CI/CD (GitHub Actions) + Husky/lint-staged
- [ ] Add i18n scaffolding (English primary, translation-ready)

### Phase 2: Product Ingestion & Embeddings
**Goal**: Build product ingestion pipeline with bootstrap store (300-500 curated products), WooCommerce API integration, FashionSigLIP embedding generation, image quality gate validation, and Qdrant as the single source of truth for product embeddings

**Depends on**: Phase 1

**Research**: Likely (external API integration, ML model usage)

**Research topics**: WooCommerce API current documentation and rate limits, FashionSigLIP embedding generation patterns and optimization, image quality validation thresholds (blur detection via Laplacian variance, dimension/size requirements)

**Plans**: TBD

Plans:
- TBD during planning

### Phase 3: Clustering & Cold Start System
**Goal**: Pre-cluster entire product catalog into 200-500 style clusters using K-means, calculate cluster priors, implement nearest cluster matching for new users based on uploaded photos

**Depends on**: Phase 2

**Research**: Likely (clustering algorithm selection, architectural decision)

**Research topics**: K-means vs HDBSCAN for fashion embedding clustering, optimal cluster count determination (silhouette analysis, elbow method), cluster prior calculation from historical data

**Plans**: TBD

Plans:
- TBD during planning

### Phase 4: User Onboarding & Profiles
**Goal**: Implement user onboarding flow with 2 outfit photo uploads, 15 calibration swipes, user profile creation, and price profiling initialization to achieve <3 minute time-to-value

**Depends on**: Phase 3

**Research**: Unlikely (photo upload is standard multipart form handling, calibration swipe logic straightforward)

**Plans**: TBD

Plans:
- TBD during planning

### Phase 5: Feed Generation & Ranking
**Goal**: Build multi-factor feed ranking system (cosine similarity 65%, cluster prior 15%, price affinity 10%, freshness 10%) with mandatory diversity injection (3/20 items from adjacent clusters) and synchronous inference with semaphore limiting (ARQ disabled in MVP)

**Depends on**: Phase 4

**Research**: Likely (algorithm design, weighting strategy validation)

**Research topics**: Multi-factor ranking approaches in recommendation systems, diversity injection techniques to prevent echo chambers, ranking weight calibration and A/B testing strategies

**Plans**: TBD

Plans:
- TBD during planning

### Phase 6: Swipe Interface & Feedback
**Goal**: Develop custom swipe component with framer-motion gesture physics, intuitive swipe animations, and feedback collection pipeline (like/dislike/save actions)

**Depends on**: Phase 5

**Research**: Unlikely (custom React component with established gesture libraries, standard event handling)

**Plans**: TBD

Plans:
- TBD during planning

### Phase 7: Learning & Personalization
**Goal**: Implement continuous learning pipeline with user vector updates using weighted centroid formula (1.0 * positive_centroid - 0.7 * negative_centroid), 14-day exponential time decay, and price affinity profiling with nightly batch updates

**Depends on**: Phase 6

**Research**: Likely (vector calculation formulas, time decay optimization)

**Research topics**: Weighted centroid methods for user preference modeling, exponential vs linear time decay functions for fashion preferences, price affinity modeling from interaction history

**Plans**: TBD

Plans:
- TBD during planning

### Phase 8: Collections & Saves
**Goal**: Build user-created collection system allowing folders for saved items ("Summer vacation", "Work outfits"), increasing engagement and emotional investment in the platform

**Depends on**: Phase 7

**Research**: Unlikely (standard CRUD operations with folder/item relationships, established UI patterns)

**Plans**: TBD

Plans:
- TBD during planning

### Phase 9: Affiliate Tracking
**Goal**: Implement end-to-end affiliate click tracking with commission attribution, partner store integration, and trackable product links to measure business model viability

**Depends on**: Phase 8

**Research**: Likely (affiliate link management, commission tracking patterns)

**Research topics**: Affiliate link generation and parameter handling, click tracking implementations (cookie vs session-based), commission attribution methods and de-duplication strategies

**Plans**: TBD

Plans:
- TBD during planning

### Phase 10: Deduplication & Data Quality
**Goal**: Deploy perceptual hashing system (pHash) to detect duplicate products from multiple stores using Hamming distance threshold of 5, preventing repetitive recommendations

**Depends on**: Phase 9

**Research**: Likely (perceptual hashing algorithms, threshold tuning)

**Research topics**: Perceptual hashing libraries (ImageHash, pHash implementations), Hamming distance threshold optimization for fashion images, duplicate detection strategies and false positive prevention

**Plans**: TBD

Plans:
- TBD during planning

### Phase 11: Analytics & Decision Logs
**Goal**: Instrument complete event taxonomy (feed views, swipes, clicks, onboarding steps) with GDPR-compliant decision logs capturing similarity scores, cluster IDs, price scores, and timestamps for every recommendation, plus data retention and right-to-erasure policies

**Depends on**: Phase 10

**Research**: Unlikely (event logging is standard database persistence, GDPR log structure already defined in requirements)

**Plans**: TBD

Plans:
- TBD during planning

### Phase 12: Performance & Caching
**Goal**: Implement Redis caching strategy for feed generation, rate limiting, optimize database queries, and establish latency monitoring to maintain p95 response times <500ms

**Depends on**: Phase 11

**Research**: Unlikely (Redis patterns well-established, standard query optimization techniques)

**Plans**: TBD

Plans:
- TBD during planning

### Phase 13: PWA Implementation
**Goal**: Configure Progressive Web App capabilities with vite-plugin-pwa, service worker for offline support, and installability on iOS and Android home screens

**Depends on**: Phase 12

**Research**: Likely (PWA specifications, platform-specific quirks)

**Research topics**: PWA manifest requirements and best practices, service worker caching strategies (cache-first vs network-first for different asset types), iOS home screen installability requirements and Safari quirks

**Plans**: TBD

Plans:
- TBD during planning

### Phase 14: Polish & Quality Assurance
**Goal**: Finalize template-based explainability system (3 templates), UX refinements, load testing with simulated 50-100 concurrent users, and edge case handling

**Depends on**: Phase 13

**Research**: Unlikely (testing and refinement of existing features, established UX patterns)

**Plans**: TBD

Plans:
- TBD during planning

### Phase 15: Launch Readiness
**Goal**: Deploy monitoring dashboards, error alerting system, complete MVP launch checklist verification, and prepare for soft launch with 50-100 users

**Depends on**: Phase 14

**Research**: Unlikely (operational setup with established monitoring tools like Prometheus/Grafana or cloud-native solutions)

**Plans**: TBD

Plans:
- TBD during planning

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Infrastructure | 7/9 | In progress | - |
| 2. Product Ingestion & Embeddings | 0/TBD | Not started | - |
| 3. Clustering & Cold Start System | 0/TBD | Not started | - |
| 4. User Onboarding & Profiles | 0/TBD | Not started | - |
| 5. Feed Generation & Ranking | 0/TBD | Not started | - |
| 6. Swipe Interface & Feedback | 0/TBD | Not started | - |
| 7. Learning & Personalization | 0/TBD | Not started | - |
| 8. Collections & Saves | 0/TBD | Not started | - |
| 9. Affiliate Tracking | 0/TBD | Not started | - |
| 10. Deduplication & Data Quality | 0/TBD | Not started | - |
| 11. Analytics & Decision Logs | 0/TBD | Not started | - |
| 12. Performance & Caching | 0/TBD | Not started | - |
| 13. PWA Implementation | 0/TBD | Not started | - |
| 14. Polish & Quality Assurance | 0/TBD | Not started | - |
| 15. Launch Readiness | 0/TBD | Not started | - |
