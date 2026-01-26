# AI Personal Stylist

## What This Is

An AI-powered fashion discovery PWA that learns the user's "Visual DNA" from wardrobe photos and swipe behavior, then shows a personalized product feed from a self-hosted WooCommerce catalog. Users swipe through products (Tinder-style) to like, dislike, or save items. For fashion-conscious shoppers who want personalized recommendations without endless scrolling.

## Core Value

**The AI recommendation must feel magical** — products shown should genuinely match the user's personal style, learned from their actual wardrobe photos and calibration swipes, not generic recommendations.

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Infrastructure (Week 1)**
- [ ] Monorepo with pnpm workspaces (apps/web, apps/backend, packages/shared)
- [ ] FastAPI backend with feature-based folder structure
- [ ] Vite + React PWA frontend with MUI
- [ ] PostgreSQL + pgvector for users, collections, embeddings
- [ ] Qdrant for vector similarity search
- [ ] Docker Compose for local development
- [ ] Cloudflare Tunnel + Traefik for production routing
- [ ] GitHub Actions CI/CD pipeline

**Authentication (Week 2)**
- [ ] Google OAuth sign-in (RS256 JWT)
- [ ] Access token (1h) + refresh token (30d)
- [ ] Protected route middleware

**AI Pipeline (Week 2)**
- [ ] Fashion-CLIP model integration (512-dim embeddings)
- [ ] Image upload to S3-compatible storage
- [ ] Qdrant collection for user styles and products

**Onboarding (Week 3)**
- [ ] Style photo upload (3+ wardrobe photos)
- [ ] Generate user style embedding from photos
- [ ] Calibration swipe (30 products)
- [ ] Refine style vector from calibration feedback

**Discovery Feed (Week 3-4)**
- [ ] Personalized product feed from WooCommerce catalog
- [ ] Vector similarity search in Qdrant
- [ ] Filter already-seen products

**Swipe Interface (Week 4)**
- [ ] Custom swipe component with framer-motion
- [ ] Swipe right = like (training signal)
- [ ] Swipe left = dislike (training signal)
- [ ] Swipe up = save to favorites
- [ ] Visual indicators during drag

**Favorites & Collections (Week 4)**
- [ ] Save products to favorites
- [ ] View saved products grid
- [ ] Create/manage collections

**PWA (Week 4-5)**
- [ ] manifest.json with app icons
- [ ] Service worker for offline support
- [ ] Installable on mobile devices

### Out of Scope

- **Search functionality** — Phase 2; MVP is pure discovery feed, no search box
- **Partner store integrations** — Phase 2; MVP uses only self-hosted WooCommerce
- **Hebrew/RTL localization** — Phase 2; MVP is English only
- **React Native apps** — Phase 3; validate with PWA first
- **Affiliate tracking/monetization** — Phase 4; focus on product-market fit first
- **Face recognition (InsightFace)** — Mentioned in spec but not needed for MVP style matching
- **Daily recommendations job** — Phase 2 feature
- **Web search for products** — Phase 2 feature

## Context

**Technical Environment:**
- Server: AMD EPYC 12-core, 48GB RAM, 1TB NVMe, Ubuntu 24.04
- Existing WooCommerce store with product catalog ready to sync
- All credentials ready: Google OAuth, Cloudflare, domain configured
- Cloudflare Tunnel for secure access without exposed ports

**Key Technical Decisions from Spec:**
- Fashion-CLIP for style embeddings (patrickjohncyh/fashion-clip, 512-dim)
- Pure vector similarity — no hardcoded fashion vocabulary
- PWA first, React Native later (faster validation)
- Monolith architecture (no microservices for MVP)
- Per-task git commits for context engineering

**Reference Documents:**
- Technical Spec: PROJECT_PLAN.md (v6.4, source of truth)
- Phase Breakdown: PROJECT_PHASES.md (Week-by-week tasks)

## Constraints

- **Tech Stack**: Must follow PROJECT_PLAN.md exactly — FastAPI, Vite+React, PostgreSQL+pgvector, Qdrant, pnpm monorepo
- **AI Runtime**: Start with PyTorch for simplicity, ONNX conversion deferred to Phase 2
- **Budget**: Self-hosted infrastructure, no expensive third-party AI APIs
- **Scope**: Phase 1 MVP only (4-5 weeks), no Phase 2+ features

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| PWA before native apps | Faster validation, no app store delays, reusable components | — Pending |
| Fashion-CLIP over custom model | Pre-trained on 700K fashion images, no training needed | — Pending |
| WooCommerce for MVP products | Already exists, full control, no partner dependencies | — Pending |
| PyTorch for MVP AI runtime | Simpler development, ONNX optimization deferred | — Pending |
| No search in MVP | Force AI quality focus, TikTok-style pure discovery | — Pending |

---
*Last updated: 2026-01-26 after initialization*
