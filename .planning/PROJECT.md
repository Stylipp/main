# AI Personal Stylist

## What This Is

A swipe-based fashion discovery PWA that delivers intelligent, personalized product recommendations from the first session. Users upload 2 outfit photos and complete 15 calibration swipes to receive a curated feed of fashion items matched to their style, powered by AI clustering and vector similarity. Revenue is generated through affiliate partnerships with fashion retailers.

## Core Value

Deliver high-quality, personalized fashion recommendations from the very first session, making style discovery feel intelligent and effortless while driving measurable affiliate revenue.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Cluster-based cold-start system using FashionSigLIP embeddings (200-500 style clusters)
- [ ] Minimal onboarding: 2 outfit photo uploads + 15 swipes for calibration
- [ ] Personalized feed ranking using multi-factor scoring (style 65%, cluster 15%, price 10%, freshness 10%)
- [ ] Swipe interaction with 3 gestures: right (like), left (dislike), up (save)
- [ ] Style Collections for saved items with user-created folders
- [ ] Weighted user vector (positive centroid - 0.7 * negative centroid) with 14-day time decay
- [ ] Price sensitivity profiling (min/max/median clicked/saved prices)
- [ ] Perceptual hashing for product deduplication (Hamming distance threshold 5)
- [ ] Affiliate tracking for click-through and revenue attribution
- [ ] Decision logging for GDPR compliance and model validation
- [ ] Partner store ingestion via WooCommerce API integration
- [ ] User authentication with JWT
- [ ] PWA with offline capabilities and home screen installation

### Out of Scope

- **Search functionality** — Deceptively complex; requires comprehensive tagging, synonym handling, fuzzy matching. Better built after collecting user behavior data. Phase 2 feature.
- **Face recognition** — Adds 30% complexity with zero core value. Creates GDPR Article 9 compliance burden, user trust issues, and technical complexity. Faces don't predict fashion preferences; outfit photos do.
- **Native mobile apps** — PWA provides 90% of the value with 40-60% lower development cost. No app store delays, instant updates, single codebase.
- **Social features** — No sharing, following, or social feed. Focus on personal discovery first; social can layer on top later.
- **Advanced explainability** — Simple explanation tags only for MVP. Full "why this recommendation" system requires complex NLP and increases development time.
- **Multiple payment methods** — Affiliate only for MVP. No direct payments, subscriptions, or premium tiers yet.

## Context

### Business Model
Affiliate revenue from fashion retailer partnerships. Every product click is tracked with affiliate codes, earning commission on resulting purchases. This allows free user access while validating commercial viability.

### User Journey
1. User uploads 2 outfit photos (their style examples)
2. System generates FashionSigLIP embeddings and maps to nearest style clusters
3. User completes 15 calibration swipes to refine preferences
4. Personal style vector is created (likes weighted positively, dislikes negatively)
5. Feed shows ranked products: similar items from their clusters + personalized matches
6. System learns continuously from all interactions (saves, swipes, clicks, time spent)
7. Recommendations improve over time while adapting to style evolution (14-day decay)

### Technical Innovation
The clustering-based cold-start solution solves the recommendation system's chicken-and-egg problem: you need user data for good recommendations, but users won't provide data if recommendations are bad. By pre-clustering all products into 200-500 style groups, even brand-new users immediately see contextually relevant items. After 10 swipes, personal learning takes over.

### Initial Inventory
Starting with one partner website that has extensive product catalog. Additional WooCommerce partners can be integrated as system scales.

### Success Metrics
- **D7 Retention**: Do users return within a week? Fashion isn't daily, but weekly return indicates value.
- **Swipe-to-Save Conversion**: Healthy ratio is 10-15% (1 in 7-10 items saved). Below 5% indicates poor recommendation quality.
- **Affiliate Click-Through Rate**: Measures commercial intent and validates whether recommendations drive actual purchasing behavior.

## Constraints

- **Tech Stack**: Fixed architecture using React 18 + Vite + MUI (frontend), FastAPI + PostgreSQL + Qdrant (backend), Docker + Cloudflare Tunnel (infrastructure). All specified in PROJECT_PLAN.md.
- **Budget**: Cost-effective infrastructure required. Using synchronous ML inference for MVP (no expensive GPU clusters), Hetzner Object Storage (S3-compatible), self-hosted Qdrant. Add complexity only when measured problems arise (p95 latency > 500ms or concurrent users > 200).
- **Open Source AI**: YOLOv8-nano (person detection), SAM (segmentation), Marqo-FashionSigLIP (style embeddings). No proprietary model dependencies.
- **Monorepo**: pnpm workspaces with feature-based architecture. Strict layer separation in backend (router → service → repository).

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Remove face recognition | Cuts 30% complexity, eliminates GDPR Article 9 burden, removes user trust barrier. Faces don't predict style preferences. | — Pending |
| Cluster-based cold-start | Enables intelligent recommendations from first session. Pre-computed style clusters (200-500) provide immediate relevance before personal learning kicks in. | — Pending |
| PWA over native apps | 40-60% lower dev cost, single codebase, no app store delays, instant updates. Acceptable tradeoffs for fashion discovery use case. | — Pending |
| Synchronous ML inference | Simple architecture for MVP (<100 users). Add async/queue complexity only when p95 latency > 500ms or concurrent users > 200. | — Pending |
| Weighted negative signals | User dislikes (β = 0.7) push recommendations away from rejected styles. More nuanced than likes-only approach. Prevents echo chambers. | — Pending |
| 14-day time decay | Recent interactions weighted higher. Adapts to evolving style preferences while filtering daily mood swings. Balance between volatility (3 days) and staleness (90 days). | — Pending |
| Products in Qdrant only | Embeddings stored in Qdrant, not duplicated in PostgreSQL. Simplifies sync, reduces costs. PostgreSQL only for user data and training logs. | — Pending |
| Affiliate-first monetization | No direct payments for MVP. Validates business model without asking users to pay. Fashion apps traditionally expect free access. | — Pending |

---
*Last updated: 2026-01-27 after initialization*
