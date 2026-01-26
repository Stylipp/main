# Roadmap: AI Personal Stylist

## Overview

Build an AI-powered fashion discovery PWA that learns users' "Visual DNA" from wardrobe photos and swipe behavior, then serves a personalized product feed from a self-hosted WooCommerce catalog. The journey goes from infrastructure setup through AI integration to a polished, installable mobile experience.

## Domain Expertise

None

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Monorepo & Docker Stack** - pnpm workspaces, Docker Compose with PostgreSQL+pgvector and Qdrant
- [ ] **Phase 2: FastAPI Backend Scaffold** - Feature-based folder structure, health endpoint, Pydantic settings
- [ ] **Phase 3: Database Foundation** - SQLAlchemy async models, Alembic migrations, pgvector extension
- [ ] **Phase 4: React PWA Shell** - Vite + React + MUI, routing, layout components
- [ ] **Phase 5: Production Infrastructure** - Cloudflare Tunnel, Traefik, GitHub Actions CI/CD
- [ ] **Phase 6: Google OAuth Authentication** - OAuth flow, RS256 JWT, token refresh, logout
- [ ] **Phase 7: Protected Routes & Auth Context** - Auth middleware, auth context, protected route wrapper
- [ ] **Phase 8: Image Storage Service** - S3-compatible storage, upload service, presigned URLs
- [ ] **Phase 9: Fashion-CLIP Model Service** - Model loading, embedding generation endpoint
- [ ] **Phase 10: Qdrant Vector Database** - Collections setup, similarity search API
- [ ] **Phase 11: WooCommerce Product Sync** - Fetch products from WooCommerce, store in PostgreSQL
- [ ] **Phase 12: Product Embedding Pipeline** - Generate embeddings for all products, store in Qdrant
- [ ] **Phase 13: Wardrobe Photo Upload** - Upload UI, generate user style embedding
- [ ] **Phase 14: Calibration Swipe Flow** - 30-product calibration, refine user style vector
- [ ] **Phase 15: Discovery Feed** - Personalized feed API and UI, exclude seen products
- [ ] **Phase 16: Swipe Interface** - Framer-motion swipe component, like/dislike/save actions
- [ ] **Phase 17: Favorites, Collections & PWA** - Save favorites, collections, PWA finalization

## Phase Details

### Phase 1: Monorepo & Docker Stack
**Goal**: Establish the development environment foundation
**Depends on**: Nothing (first phase)
**Research**: Unlikely (standard pnpm and Docker patterns)
**Plans**: TBD

**Deliverables:**
- pnpm workspaces with `apps/web`, `apps/backend`, `packages/shared`
- Docker Compose with PostgreSQL + pgvector, Qdrant containers
- Shared TypeScript config, ESLint, Prettier
- `pnpm install` and `docker-compose up` work

### Phase 2: FastAPI Backend Scaffold
**Goal**: Create the backend application structure
**Depends on**: Phase 1
**Research**: Unlikely (established FastAPI patterns)
**Plans**: TBD

**Deliverables:**
- Feature-based folder structure (`/features/auth`, `/features/products`, etc.)
- Health endpoint at `/api/health`
- Pydantic settings for environment config
- Backend responds to health checks

### Phase 3: Database Foundation
**Goal**: Set up database models and migrations
**Depends on**: Phase 2
**Research**: Likely (pgvector setup, async SQLAlchemy)
**Research topics**: pgvector extension installation, SQLAlchemy async patterns with PostgreSQL
**Plans**: TBD

**Deliverables:**
- SQLAlchemy async models (users, products, favorites, collections)
- Alembic migrations setup
- pgvector extension enabled
- Migrations run, tables created

### Phase 4: React PWA Shell
**Goal**: Create the frontend application structure
**Depends on**: Phase 1
**Research**: Unlikely (standard Vite + React + MUI)
**Plans**: TBD

**Deliverables:**
- Vite + React + TypeScript setup
- MUI theme with dark/light mode
- React Router with routes (/, /login, /onboarding, /feed, /favorites)
- Frontend renders with navigation

### Phase 5: Production Infrastructure
**Goal**: Enable secure production deployment
**Depends on**: Phase 2, Phase 4
**Research**: Likely (Cloudflare Tunnel, Traefik configuration)
**Research topics**: Cloudflare Tunnel setup, Traefik with Docker, GitHub Actions deployment workflows
**Plans**: TBD

**Deliverables:**
- Cloudflare Tunnel configuration
- Traefik reverse proxy with SSL termination
- GitHub Actions CI/CD (lint, test, build, deploy)
- App accessible via HTTPS domain, PRs trigger checks

### Phase 6: Google OAuth Authentication
**Goal**: Implement user authentication with Google
**Depends on**: Phase 3, Phase 5
**Research**: Likely (Google OAuth, RS256 JWT)
**Research topics**: Google OAuth 2.0 flow, python-jose RS256 implementation, refresh token patterns
**Plans**: TBD

**Deliverables:**
- Google OAuth consent screen and credentials
- Authorization endpoint, callback handler
- RS256 JWT generation (access 1h, refresh 30d)
- Token refresh endpoint, logout
- Users can sign in with Google, sessions persist

### Phase 7: Protected Routes & Auth Context
**Goal**: Secure application routes for authenticated users only
**Depends on**: Phase 6
**Research**: Unlikely (follows patterns from Phase 6)
**Plans**: TBD

**Deliverables:**
- Backend auth middleware (verify JWT, extract user)
- Frontend auth context and hooks
- Protected route wrapper component
- Redirect unauthenticated users to login
- Only authenticated users access protected pages

### Phase 8: Image Storage Service
**Goal**: Enable image uploads with CDN delivery
**Depends on**: Phase 7
**Research**: Likely (S3-compatible storage)
**Research topics**: MinIO setup for development, boto3 presigned URLs, image optimization
**Plans**: TBD

**Deliverables:**
- S3-compatible storage setup (MinIO for dev, S3 for prod)
- Upload service with presigned URLs
- Image validation and optimization
- Images upload and serve via CDN

### Phase 9: Fashion-CLIP Model Service
**Goal**: Generate visual embeddings for fashion images
**Depends on**: Phase 2
**Research**: Likely (Fashion-CLIP API, PyTorch)
**Research topics**: Fashion-CLIP model usage (patrickjohncyh/fashion-clip), PyTorch model loading, batch inference
**Plans**: TBD

**Deliverables:**
- Load Fashion-CLIP model (patrickjohncyh/fashion-clip)
- Embedding generation endpoint (image → 512-dim vector)
- Batch processing for multiple images
- POST image returns embedding vector

### Phase 10: Qdrant Vector Database
**Goal**: Enable vector similarity search
**Depends on**: Phase 9
**Research**: Likely (Qdrant Python client)
**Research topics**: Qdrant collection configuration, similarity search API, filtering and pagination
**Plans**: TBD

**Deliverables:**
- Create collections: `user_styles`, `products`
- Upsert and query operations
- Similarity search with filtering
- Vector similarity queries work

### Phase 11: WooCommerce Product Sync
**Goal**: Import product catalog from WooCommerce
**Depends on**: Phase 3
**Research**: Likely (WooCommerce REST API)
**Research topics**: WooCommerce API authentication, product endpoints, pagination handling
**Plans**: TBD

**Deliverables:**
- WooCommerce REST API integration
- Fetch all products with images, prices, metadata
- Store in PostgreSQL products table
- Sync job for updates
- Products table populated from WooCommerce

### Phase 12: Product Embedding Pipeline
**Goal**: Make all products searchable by visual similarity
**Depends on**: Phase 10, Phase 11
**Research**: Unlikely (uses patterns from phases 9-10)
**Plans**: TBD

**Deliverables:**
- Generate Fashion-CLIP embeddings for all product images
- Store embeddings in Qdrant `products` collection
- Progress tracking for batch processing
- All products searchable by visual similarity

### Phase 13: Wardrobe Photo Upload
**Goal**: Capture user's personal style from wardrobe photos
**Depends on**: Phase 8, Phase 10
**Research**: Unlikely (uses patterns from Phase 8)
**Plans**: TBD

**Deliverables:**
- Photo upload UI (drag-drop, mobile camera)
- Require minimum 3 photos
- Generate user style embedding (average of photo embeddings)
- Store in Qdrant `user_styles` collection
- Users upload wardrobe, get style vector

### Phase 14: Calibration Swipe Flow
**Goal**: Refine user style through explicit preferences
**Depends on**: Phase 12, Phase 13
**Research**: Unlikely (internal UI patterns)
**Plans**: TBD

**Deliverables:**
- Show 30 diverse products for calibration
- Simple swipe UI (like/dislike only)
- Record preferences
- Refine user style vector from feedback (weighted average)
- Calibration improves style matching

### Phase 15: Discovery Feed
**Goal**: Serve personalized product recommendations
**Depends on**: Phase 14
**Research**: Unlikely (uses established patterns)
**Plans**: TBD

**Deliverables:**
- Feed API: query Qdrant with user style vector
- Exclude already-seen products
- Pagination with cursor
- Feed UI: product cards, infinite scroll, loading states
- Users see personalized product feed

### Phase 16: Swipe Interface
**Goal**: Implement Tinder-style swipe interactions
**Depends on**: Phase 15
**Research**: Likely (framer-motion gestures)
**Research topics**: framer-motion drag gestures, swipe detection thresholds, spring animations
**Plans**: TBD

**Deliverables:**
- Framer-motion swipe component
- Swipe right = like (positive training signal)
- Swipe left = dislike (negative training signal)
- Swipe up = save to favorites
- Visual drag indicators, haptic feedback
- Tinder-style swipe interaction works

### Phase 17: Favorites, Collections & PWA
**Goal**: Complete the MVP with collections and PWA features
**Depends on**: Phase 16
**Research**: Likely (PWA patterns)
**Research topics**: PWA manifest configuration, service worker caching strategies, install prompt handling
**Plans**: TBD

**Deliverables:**
- Save to favorites, favorites grid view
- Create/edit/delete collections
- Add/remove products from collections
- PWA manifest.json with icons
- Service worker for offline support
- Install prompt on mobile
- Full PWA installable with collections feature

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → ... → 17

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Monorepo & Docker Stack | 0/TBD | Not started | - |
| 2. FastAPI Backend Scaffold | 0/TBD | Not started | - |
| 3. Database Foundation | 0/TBD | Not started | - |
| 4. React PWA Shell | 0/TBD | Not started | - |
| 5. Production Infrastructure | 0/TBD | Not started | - |
| 6. Google OAuth Authentication | 0/TBD | Not started | - |
| 7. Protected Routes & Auth Context | 0/TBD | Not started | - |
| 8. Image Storage Service | 0/TBD | Not started | - |
| 9. Fashion-CLIP Model Service | 0/TBD | Not started | - |
| 10. Qdrant Vector Database | 0/TBD | Not started | - |
| 11. WooCommerce Product Sync | 0/TBD | Not started | - |
| 12. Product Embedding Pipeline | 0/TBD | Not started | - |
| 13. Wardrobe Photo Upload | 0/TBD | Not started | - |
| 14. Calibration Swipe Flow | 0/TBD | Not started | - |
| 15. Discovery Feed | 0/TBD | Not started | - |
| 16. Swipe Interface | 0/TBD | Not started | - |
| 17. Favorites, Collections & PWA | 0/TBD | Not started | - |
