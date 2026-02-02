# Stylipp MVP Plan — Deep Analysis & Expanded Explanations

**Analysis Version:** 2.1  
**Date:** January 2026  
**Purpose:** Comprehensive review and expanded context for each planning element

---

## Critical Fixes in v2.1

| Issue | Risk | Fix Applied |
|-------|------|-------------|
| **YOLOv8 AGPL license** | Legal copyleft risk | Removed; skip detection in MVP, use RT-DETR (Apache) in Phase 2 |
| **Redis + ARQ contradiction** | Premature complexity | ARQ disabled; Redis for caching only |
| **Explainability too ambitious** | Scope creep | 3 simple templates only |
| **Partner dependency** | Week 1 blocker | Bootstrap store fallback (300-500 products) |
| **No image quality gate** | Garbage embeddings | Added blur/size/dimension checks |
| **No diversity injection** | Echo chambers | Force 3 items per 20 from adjacent clusters |
| **No analytics** | Can't debug | Full event taxonomy from day one |

---

## Executive Summary: My Overall Assessment

This is a **well-crafted, pragmatic MVP plan** that demonstrates mature startup thinking. The most impressive aspect is what you've chosen to *remove* rather than what you've included. The decision to eliminate face recognition cuts approximately 30% of the complexity while losing zero core value. This is the kind of ruthless prioritization that separates successful MVPs from bloated projects that never ship.

**Key Strengths:**
- Realistic scope that can actually be built in 6 weeks
- Elegant cold-start solution using clustering
- Clear monetization path from day one
- Infrastructure decisions that scale gracefully
- Strong focus on the metrics that actually matter

**Areas to Watch:**
- Partner store dependency could be a bottleneck
- 15 swipes may still feel like work to some users
- Price sensitivity assumes users have consistent budgets
- Explainability implementation is harder than it looks

---

## Technology Stack (Updated)

### Frontend (web)
| Component | Choice |
|-----------|--------|
| Framework | React 18 |
| Build Tool | Vite |
| Styling | MUI (Material UI) v5 |
| State Management | Zustand |
| Server State | TanStack Query (React Query) |
| HTTP Client | Axios |
| Router | React Router v6 |
| Forms | React Hook Form + Zod |
| Swipe UI | Custom Component (framer-motion) |
| PWA | vite-plugin-pwa |
| Language | TypeScript |

### Backend
| Component | Choice | MVP Status |
|-----------|--------|------------|
| Framework | FastAPI | ✅ Active |
| Database | PostgreSQL (no pgvector in MVP) | ✅ Active |
| Vector Store | Qdrant | ✅ Active |
| ORM | SQLAlchemy 2.0 (async) | ✅ Active |
| Migrations | Alembic | ✅ Active |
| Cache | Redis | ✅ Active (caching only) |
| Task Queue | ARQ | ⏸️ Disabled in MVP |
| Storage | Hetzner Object Storage (S3 compatible) | ✅ Active |
| Auth | JWT (python-jose) | ✅ Active |
| Validation | Pydantic v2 | ✅ Active |
| Language | Python 3.12+ | ✅ Active |

**⚠️ MVP Clarifications:**

**Redis (MVP):** Used ONLY for:
- Session/token caching
- Rate limiting
- Feed result caching (short TTL)

**ARQ (Phase 2):** Task queue disabled in MVP. All inference is synchronous with semaphore limiting. Enable ARQ when:
- p95 latency > 500ms
- Concurrent users > 200
- Background jobs needed (email, reports)

**PostgreSQL (MVP):**
- No pgvector extension in MVP
- Postgres stores: users, feedback, user style snapshots, decision logs
- Does NOT store product embeddings (those live in Qdrant only)
- Revisit pgvector only if needed in Phase 2+

### AI Models (Open Source — All Permissive Licenses)
| Model | Purpose | License | Notes |
|-------|---------|---------|-------|
| Marqo-FashionSigLIP | Style embedding | Apache 2.0 | Core model |
| SAM | Segmentation | Apache 2.0 | Phase 2 |
| RT-DETR | Person detection | Apache 2.0 | Phase 2 (if needed) |

**⚠️ AGPL Avoidance Policy:**  
YOLOv8 (AGPL-3.0) was intentionally excluded due to copyleft obligations that create legal risk for proprietary SaaS. All models must be Apache 2.0, MIT, or similarly permissive.

**MVP Person Detection Strategy:**  
For MVP, skip person detection entirely. Users upload outfit photos—embed the whole image with FashionSigLIP. This works well enough for MVP because:
- Users self-select relevant photos
- FashionSigLIP is trained on fashion images and handles full-frame clothing well
- Saves 2-3 weeks of detection pipeline work

Add person detection (RT-DETR or similar) in Phase 2 only if:
- User uploads contain too much background noise
- Embedding quality metrics show degradation on full-frame images

### Infrastructure
| Component | Choice |
|-----------|--------|
| Monorepo | pnpm workspaces |
| Reverse Proxy | Traefik |
| Tunnel | Cloudflare Tunnel |
| Containers | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Git Hooks | Husky |

---

## Monorepo Structure

```
📦 Stylipp/
├── 📁 apps/
│   ├── 📁 web/                  ← Vite + React PWA
│   ├── 📁 backend/              ← FastAPI
│   └── 📁 mobile/               ← React Native (Phase 2 - Future)
├── 📁 packages/
│   └── 📁 shared/               ← Shared types, models, utils
├── 📁 infra/
│   └── 📄 docker-compose.yml
│   └── 📁 cloudflare/           ← Cloudflare Tunnel config
├── 📁 scripts/                  ← Deploy, setup scripts
├── 📁 .github/workflows/        ← CI/CD Pipelines
├── 📁 .husky/                   ← Git hooks
├── 📄 package.json              ← Root pnpm workspace
├── 📄 pnpm-workspace.yaml
└── 📁 docs/                     ← Documentation
```

---

## Frontend Architecture (Feature-Based)

```
📁 apps/web/
├── 📁 src/
│   ├── 📁 features/
│   │   ├── 📁 auth/
│   │   │   ├── 📁 api/          ← API calls
│   │   │   ├── 📁 components/   ← UI components
│   │   │   ├── 📁 pages/        ← Route pages
│   │   │   ├── 📁 routes/       ← Route definitions
│   │   │   ├── 📁 store/        ← Zustand slices
│   │   │   ├── 📁 types/        ← TypeScript types
│   │   │   └── 📁 utils/        ← Helper functions
│   │   ├── 📁 onboarding/
│   │   │   ├── 📁 api/
│   │   │   ├── 📁 components/
│   │   │   ├── 📁 pages/
│   │   │   ├── 📁 routes/
│   │   │   ├── 📁 store/
│   │   │   ├── 📁 types/
│   │   │   └── 📁 utils/
│   │   ├── 📁 feed/
│   │   │   ├── 📁 api/
│   │   │   ├── 📁 components/
│   │   │   │   └── 📁 swipe/    ← Custom swipe component
│   │   │   ├── 📁 pages/
│   │   │   ├── 📁 routes/
│   │   │   ├── 📁 store/
│   │   │   ├── 📁 types/
│   │   │   └── 📁 utils/
│   │   ├── 📁 favorites/
│   │   └── 📁 profile/
│   ├── 📁 shared/               ← Shared across features
│   │   ├── 📁 components/       ← Common UI components
│   │   ├── 📁 hooks/            ← Custom hooks
│   │   ├── 📁 utils/            ← Helper functions
│   │   ├── 📁 types/            ← Shared types
│   │   └── 📁 theme/            ← MUI theme config
│   ├── 📁 lib/                  ← External integrations
│   ├── 📄 App.tsx
│   ├── 📄 main.tsx
│   └── 📄 router.tsx
├── 📁 public/
│   ├── 📄 manifest.json         ← PWA config
│   └── 📁 icons/
├── 📄 index.html
├── 📄 vite.config.ts
├── 📄 tsconfig.json
└── 📄 package.json
```

---

## Backend Architecture (Feature-Based)

```
📁 apps/backend/
├── 📁 src/
│   ├── 📁 features/
│   │   ├── 📁 auth/
│   │   │   ├── 📄 router.py     ← Route definitions only
│   │   │   ├── 📄 service.py    ← Business logic only
│   │   │   ├── 📄 repository.py ← DB operations only
│   │   │   ├── 📄 schemas.py    ← Pydantic schemas
│   │   │   ├── 📄 utils.py      ← Helper functions
│   │   │   └── 📄 __init__.py
│   │   ├── 📁 onboarding/
│   │   │   ├── 📄 router.py
│   │   │   ├── 📄 service.py
│   │   │   ├── 📄 repository.py
│   │   │   ├── 📄 schemas.py
│   │   │   └── 📄 utils.py
│   │   ├── 📁 feed/
│   │   │   ├── 📄 router.py
│   │   │   ├── 📄 service.py
│   │   │   ├── 📄 repository.py
│   │   │   ├── 📄 schemas.py
│   │   │   └── 📄 utils.py
│   │   ├── 📁 products/
│   │   ├── 📁 favorites/
│   │   ├── 📁 style/
│   │   │   ├── 📄 router.py
│   │   │   ├── 📄 service.py    ← AI inference logic
│   │   │   ├── 📄 repository.py ← Qdrant operations
│   │   │   ├── 📄 schemas.py
│   │   │   └── 📄 utils.py
│   │   └── 📁 affiliate/
│   ├── 📁 core/                 ← Shared across features
│   │   ├── 📄 config.py         ← Settings
│   │   ├── 📄 database.py       ← DB connection
│   │   ├── 📄 security.py       ← Auth utilities
│   │   ├── 📄 dependencies.py   ← FastAPI dependencies
│   │   └── 📄 exceptions.py     ← Custom exceptions
│   ├── 📁 models/               ← SQLAlchemy models
│   │   ├── 📄 user.py
│   │   ├── 📄 product.py
│   │   ├── 📄 feedback.py
│   │   └── 📄 __init__.py
│   ├── 📁 services/             ← External services
│   │   ├── 📄 storage.py        ← Hetzner S3
│   │   ├── 📄 qdrant.py         ← Vector DB
│   │   └── 📄 redis.py          ← Cache
│   └── 📄 main.py
├── 📁 migrations/               ← Alembic
├── 📁 tests/
├── 📄 requirements.txt
├── 📄 pyproject.toml
└── 📄 Dockerfile
```

### Backend Strict Separation Rules

| Layer | Responsibility | Can Access |
|-------|---------------|------------|
| **router.py** | HTTP handling, request/response | service only |
| **service.py** | Business logic | repository, external services |
| **repository.py** | Database operations | models, Qdrant |
| **utils.py** | Helper functions | nothing (pure functions) |
| **schemas.py** | Request/response validation | nothing |

---

## Shared Package Structure

```
📁 packages/shared/
├── 📁 src/
│   ├── 📁 types/
│   │   ├── 📄 product.ts
│   │   ├── 📄 user.ts
│   │   ├── 📄 api.ts
│   │   └── 📄 index.ts
│   ├── 📁 constants/
│   │   ├── 📄 errors.ts
│   │   └── 📄 index.ts
│   └── 📄 index.ts
├── 📄 package.json
└── 📄 tsconfig.json
```

```typescript
// packages/shared/src/types/product.ts
export interface Product {
  id: string;
  title: string;
  imageUrl: string;
  price: number;
  currency: string;
  storeName: string;
  storeUrl: string;
  affiliateUrl?: string;
  brandId?: string;
  storeId?: string;
  similarityScore?: number;
  inStock: boolean;
}

export interface SavedProduct extends Product {
  savedAt: string;
  sizesAvailable?: string[];
  colorsAvailable?: string[];
}
```

```typescript
// packages/shared/src/types/api.ts
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  error?: ApiError;
}

export interface ApiError {
  code: string;
  message: string;
  userMessage: string;
  userMessageHe: string;
}

export type SwipeFeedback = 'liked' | 'disliked' | 'saved';

export interface SwipeRequest {
  productId: string;
  feedback: SwipeFeedback;
  positionInFeed: number;
  timeSpentMs: number;
}

export interface FeedResponse {
  products: Product[];
  remaining: number;
  nextCursor?: string;
}
```

---

## 1. Strategic Objective — Deep Dive

### Why These Specific Goals Matter

**"High-quality recommendations from first session"** — This is the make-or-break moment for any recommendation app. Users form their opinion of your AI's intelligence within the first 30 seconds. If the first 5 items shown are irrelevant, users assume the app is dumb and leave. They won't give you 50 swipes to "train" the algorithm. The clustering approach directly addresses this by ensuring even brand-new users see contextually relevant items.

**"Minimize onboarding friction"** — Every step in onboarding has a drop-off rate. Industry data suggests:
- Each additional screen loses 10-20% of users
- Each required action (photo upload, account creation) loses 15-30%
- Time-to-value over 60 seconds dramatically increases abandonment

Your reduction from 3 photos + 50 swipes to 2 photos + 15 swipes isn't just a small improvement—it could double your onboarding completion rate.

**"Control infrastructure cost"** — This is where many AI startups fail. They build for scale before they have users, burning runway on GPU clusters serving nobody. Your synchronous inference approach for early users is correct. A single CPU can handle Fashion-CLIP inference for dozens of concurrent users. You don't need Kubernetes and auto-scaling until you have the problem of too many users.

**"Collect clean training data"** — This is playing the long game. Every swipe, save, and click becomes training data for future model improvements. But only if you structure it correctly from day one. Retrofitting data collection is painful and often results in biased or incomplete datasets.

**"Monetizable from day one"** — Affiliate revenue means you don't need users to pay directly. This is crucial for fashion apps where users expect free access. You can validate product-market fit without the confounding variable of "are they willing to pay?"

### Why D7 Retention + Swipe-to-Save Conversion

**D7 (Day 7) Retention** measures whether users return after a week. Why a week? Fashion isn't a daily need. Users might browse when they're bored, planning an outfit, or have upcoming events. A week captures at least one natural use occasion for most people. If they don't return within 7 days, they've likely forgotten about you.

**Swipe-to-Save Conversion** is a quality signal. High swipe volume with low saves means users are seeing lots of items but finding nothing worth keeping. This indicates poor recommendation quality. A healthy ratio might be 10-15% (save roughly 1 in 7-10 items seen). Below 5% suggests serious algorithm problems.

### What I'd Add

Consider tracking **affiliate click-through rate** as a secondary metric. This measures commercial intent and validates whether your recommendations drive purchasing behavior, not just browsing. You can have great engagement metrics while showing items users would never actually buy.

---

## 2. Product Scope — Expanded Reasoning

### Why PWA (Progressive Web App) Over Native Apps

**Development Economics:** Building and maintaining native iOS and Android apps requires essentially three codebases (iOS, Android, backend). A PWA is one codebase that works everywhere. For MVP, this means:
- 40-60% lower development cost
- Single deployment pipeline
- No App Store review delays (critical for rapid iteration)
- Updates deploy instantly to all users

**User Acquisition:** Native apps require convincing users to go to an app store, search, download, wait, and open. PWAs can be accessed via link and optionally "installed" to home screen. This dramatically lowers the barrier to first use.

**Technology Choice: Vite + React + MUI**
- **Vite**: Fastest build tool, excellent HMR, optimized production builds
- **React**: Familiar ecosystem, large component library
- **MUI**: Production-ready components, consistent design, great accessibility
- **Custom Swipe Component**: Full control over UX, no dependency issues, tailored to exact needs

**Tradeoffs to Accept:** PWAs have limitations—slightly worse performance, no push notifications on iOS (though this is changing), limited offline capabilities, and less access to device hardware. For a fashion discovery app that primarily shows images and tracks swipes, these limitations are acceptable.

### Why Swipe-Based Discovery Without Search (MVP)

**Search is Deceptively Complex:** A good search experience requires:
- Comprehensive product tagging (colors, styles, occasions, materials)
- Synonym handling ("sneakers" = "trainers" = "athletic shoes")
- Spelling correction and fuzzy matching
- Ranking by relevance, not just keyword match
- Handling queries with no results gracefully

Building search well is a 4-6 week project on its own. Building search poorly is worse than having no search—users will search, find nothing, and conclude your inventory is limited.

**Discovery Creates Different Value:** Swipe-based discovery is about serendipity—finding things you didn't know you wanted. This is actually more valuable for fashion because users often can't articulate what they're looking for. "I want something for a casual dinner but not too casual" is hard to search for but easy to recognize when swiped.

**Search is Phase 2:** Once you have user behavior data and robust product metadata, search becomes much easier to build well. Keep it in the roadmap but not in MVP.

### Why Remove Face Recognition — The Crucial Decision

This deserves special emphasis because it demonstrates excellent product judgment. Here's what face recognition would have added to the project:

**Technical Complexity:**
- InsightFace model integration and optimization
- Face detection, alignment, and embedding extraction
- Identity vector storage and matching
- Handling edge cases (multiple faces, partial faces, poor lighting)

**Legal and Compliance Burden:**
- Biometric data falls under GDPR Article 9 (special category data requiring explicit consent)
- Illinois BIPA and similar state laws in the US have strict biometric requirements
- Age estimation from faces creates liability (what if you show adult content to a minor?)
- Data breach involving biometric data has severe consequences

**User Trust Barriers:**
- Many users are uncomfortable uploading face photos to apps
- "Why does a fashion app need my face?" creates suspicion
- Privacy-conscious users will abandon during onboarding

**The Key Insight:** Face recognition answers "who is this person?" but your app needs to answer "what style does this person like?" These are completely different problems. A person's face tells you nothing about their fashion preferences. Their outfit photos tell you everything you need.

### What Stays and Why It Matters

**Partner Store Ingestion (WooCommerce):** This is your inventory source. Without products to show, you have no app. Starting with WooCommerce partners is smart because:
- Large ecosystem of fashion stores
- Standardized product data format
- Existing affiliate programs
- No need to build web crawlers

### ⚠️ Partner Dependency Fallback Strategy

**Problem:** Partner negotiations can drag. You cannot let Week 1 be blocked.

**Solution: Bootstrap Store**

Create a dummy WooCommerce store YOU control with 300-500 curated products:
1. Source royalty-free fashion images (Unsplash, Pexels)
2. Or scrape public product images (for internal testing only)
3. Generate realistic metadata (prices, descriptions)
4. This becomes your dev/test dataset

**Timeline:**
| Week | Partner Status | Fallback |
|------|---------------|----------|
| 1-2 | Negotiating | Use bootstrap store |
| 3-4 | Integration testing | Parallel: bootstrap + 1 real partner |
| 5+ | Live | Real partners, deprecate bootstrap |

**Bootstrap Store Spec:**
- 300-500 products minimum
- At least 5 categories (tops, bottoms, dresses, shoes, accessories)
- Price range $20-$500
- Mix of styles (casual, formal, streetwear, minimalist)

This ensures you're never blocked on external dependencies.

**Marqo-FashionSigLIP Embeddings:** This is the core AI technology. FashionSigLIP (a fine-tuned vision model for fashion) converts images into numerical vectors that capture style characteristics. Two items with similar vectors have similar styles. This enables the entire recommendation system.

**Qdrant Vector Search:** Purpose-built database for finding similar vectors quickly. When a user has a style preference (represented as a vector), Qdrant finds products with similar vectors in milliseconds. This is the engine that powers recommendations.

**Affiliate Tracking:** Your business model. Every click to a partner store needs tracking so you get credit for sales you drive. This must work correctly from day one.

**Style Collections:** User-created folders for saved items. "Summer vacation," "Work outfits," "Date night." This increases engagement and creates emotional investment in the app.

---

## 3. Cold-Start & Style Bootstrap — The Critical Innovation

### Understanding the Cold-Start Problem

Cold-start is the chicken-and-egg problem of recommendation systems. You need user data to make good recommendations, but users won't provide data if recommendations are bad. Traditional approaches all have flaws:

**Ask Many Questions:** "What's your style? Casual? Formal? What colors do you like?" This is slow, users lie or don't know their own preferences, and answers don't translate well to specific recommendations.

**Show Popular Items:** Works for mainstream taste but alienates users with distinctive style. If someone has alternative fashion sense, showing them bestsellers signals "this app isn't for me."

**Show Random Items:** Honest but terrible. Users assume the app is stupid.

### How Global Style Clustering Solves This

The insight is that fashion styles, while diverse, cluster into recognizable groups. Think of it this way: there isn't infinite variation in how people dress. There's streetwear, there's minimalist Scandinavian, there's bohemian, there's preppy, there's athleisure, there's vintage, and so on. Each of these has subcategories, but the total number of distinct style clusters is probably in the hundreds, not millions.

**The Preprocessing Step:** Before any user arrives, you analyze your entire product catalog:
1. Convert every product image to a FashionSigLIP embedding (a vector of numbers representing its style)
2. Run clustering algorithms (K-Means or HDBSCAN) to group similar products
3. End up with 200-500 distinct style clusters, each with a "center point" (centroid)

**Why HDBSCAN Might Be Better Than K-Means:** K-Means requires you to specify the number of clusters in advance. HDBSCAN discovers clusters organically based on density. Fashion styles aren't equally common—there might be one huge "casual basics" cluster and many small niche clusters. HDBSCAN handles this naturally.

**The First Session Experience:** When a new user uploads 2 outfit photos:
1. Convert their photos to FashionSigLIP embeddings
2. Find the 3 nearest cluster centroids to their photos
3. Show products from those clusters

This means a user who uploads minimalist outfits immediately sees minimalist products. A user who uploads streetwear immediately sees streetwear. The app appears intelligent from the first item shown.

**The 10-Swipe Threshold:** After 10 swipes, you have actual preference data (likes and dislikes). Now you can start building a personal style vector that's more accurate than cluster membership alone. The clusters got them started; personal learning takes over.

### Why 200-500 Clusters?

Too few clusters (say, 20) would be too broad—"casual" isn't specific enough. Too many clusters (say, 5000) would have sparse membership and make the system fragile. 200-500 provides enough granularity to capture meaningful style distinctions while having enough products per cluster to generate varied recommendations.

The exact number should be determined empirically by looking at:
- Average cluster size (want at least 50-100 products per cluster)
- Intra-cluster similarity (items in a cluster should actually look similar)
- Inter-cluster distinction (clusters should be noticeably different from each other)

---

## 4. Onboarding Flow — Psychology of First Impressions

### Why the Original Flow Was Too Heavy

**3 Photos + 50 Swipes Analysis:**
- 3 photos: Users must find 3 suitable outfit photos in their camera roll, crop them appropriately, and upload. This takes 2-5 minutes and requires cognitive effort ("which photos best represent my style?")
- 50 swipes: At 3 seconds per swipe, this is 2.5 minutes of focused attention on a brand-new app that hasn't proven its value yet

Total time-to-value: 5-8 minutes. Research consistently shows that mobile app users expect value within 60 seconds. You were asking for 5-8 minutes of work before showing personalized results.

### Why the New Flow Works Better

**2 Photos + 15 Swipes Analysis:**
- 2 photos: Meaningfully easier than 3. Users often have 1-2 "good outfit" photos readily accessible. Asking for 3 often requires digging.
- 15 swipes: Under a minute. This feels like exploring, not working.

Total time-to-value: 2-3 minutes. Still longer than ideal, but the cluster-based bootstrap means the first recommendations (even before personal learning) are already relevant.

### The Silent Learning Principle

After initial calibration, the system continues learning from every interaction without asking the user to do anything explicit. This is crucial because:

**Conscious vs. Unconscious Preferences:** Users often can't articulate their preferences accurately. They might say they like "classic style" but consistently save edgier items. Silent learning captures actual behavior, not stated preferences.

**Effort Budget:** Users have limited patience for explicit feedback. Every "rate this item" prompt depletes their goodwill. By learning silently from natural actions (viewing time, saves, clicks), you gather data without asking for it.

**Perceived Intelligence:** When the app improves without obvious training, users attribute intelligence to it. "It just knows what I like" is the goal.

---

## 4.5. Image Quality Gate — Preventing Garbage Embeddings

### Why This Matters

Bad input = bad embeddings = bad recommendations = user churn. Users upload all kinds of images:
- Blurry photos
- Too dark / overexposed
- Tiny thumbnails
- Screenshots of screenshots
- Group photos where outfit is 10% of frame

If you embed these, you pollute the user's style vector from day one.

### MVP Implementation

```python
# apps/backend/src/features/onboarding/utils.py
from PIL import Image
import numpy as np

class ImageQualityGate:
    MIN_DIMENSION = 400  # pixels
    MIN_FILE_SIZE = 50_000  # 50KB
    MAX_FILE_SIZE = 10_000_000  # 10MB
    BLUR_THRESHOLD = 100  # Laplacian variance
    
    @staticmethod
    def check_dimensions(img: Image.Image) -> tuple[bool, str]:
        w, h = img.size
        if w < ImageQualityGate.MIN_DIMENSION or h < ImageQualityGate.MIN_DIMENSION:
            return False, "image_too_small"
        return True, ""
    
    @staticmethod
    def check_blur(img: Image.Image) -> tuple[bool, str]:
        """Laplacian variance - low = blurry"""
        gray = img.convert('L')
        arr = np.array(gray)
        laplacian_var = np.var(np.abs(np.fft.laplace(arr)))
        if laplacian_var < ImageQualityGate.BLUR_THRESHOLD:
            return False, "image_too_blurry"
        return True, ""
    
    @staticmethod
    def validate(img: Image.Image, file_size: int) -> tuple[bool, str | None]:
        if file_size < ImageQualityGate.MIN_FILE_SIZE:
            return False, "file_too_small"
        if file_size > ImageQualityGate.MAX_FILE_SIZE:
            return False, "file_too_large"
        
        ok, reason = ImageQualityGate.check_dimensions(img)
        if not ok:
            return False, reason
            
        ok, reason = ImageQualityGate.check_blur(img)
        if not ok:
            return False, reason
        
        return True, None
```

### User-Friendly Error Messages

```typescript
const qualityErrors: Record<string, { en: string; he: string }> = {
  image_too_small: {
    en: "This image is too small. Please upload a larger photo.",
    he: "התמונה קטנה מדי. אנא העלה תמונה גדולה יותר."
  },
  image_too_blurry: {
    en: "This image is a bit blurry. Try a clearer photo?",
    he: "התמונה מטושטשת. נסה תמונה חדה יותר?"
  },
  file_too_small: {
    en: "This file is too small. Please upload a higher quality image.",
    he: "הקובץ קטן מדי. אנא העלה תמונה באיכות גבוהה יותר."
  },
  file_too_large: {
    en: "This file is too large. Please upload an image under 10MB.",
    he: "הקובץ גדול מדי. אנא העלה תמונה עד 10MB."
  },
};
```

### Gate Placement

```
User uploads image
        │
        ▼
  ┌─────────────┐
  │ Size check  │──── Fail ────► "File too small/large"
  └─────────────┘
        │ Pass
        ▼
  ┌─────────────┐
  │ Dimensions  │──── Fail ────► "Image too small"
  └─────────────┘
        │ Pass
        ▼
  ┌─────────────┐
  │ Blur check  │──── Fail ────► "Image too blurry"
  └─────────────┘
        │ Pass
        ▼
  Generate embedding
```

---

## 5. Style Representation — The Math Behind Taste

### Why Simple Centroids Aren't Enough

The naive approach to representing user style would be: average all the items they liked. This creates a "centroid" (center point) of their preferences. The problem is that this ignores what they disliked.

**Example:** Imagine a user who loves both minimalist basics AND bold statement pieces, but hates anything in between. A simple average of their likes would point to the middle ground—exactly what they hate.

### The Weighted Vector Formula Explained

The formula `user_vector = α * positive_centroid - β * negative_centroid` does something clever:

**Positive Centroid (α = 1.0):** The average of everything they liked, with full weight.

**Negative Centroid (β = 0.7):** The average of everything they disliked, subtracted with 0.7 weight.

**Why 0.7 and not 1.0?** Psychological research shows that dislikes are more informative than likes for personalization. If someone dislikes an item, they definitely don't want similar items. If someone likes an item, they might like variations. But you don't want negative signals to completely dominate (which would happen at β = 1.0 or higher), so 0.7 balances the effect.

**The Result:** The user vector points toward what they like AND away from what they dislike. This creates more nuanced recommendations than considering likes alone.

### Time Decay — Evolving Style

Fashion preferences aren't static. What someone loved last year might not appeal to them now. The time decay formula ensures recent interactions matter more than old ones.

**The Half-Life Concept:** With τ = 14 days, an interaction from 14 days ago has about 37% of the weight of an interaction from today. An interaction from a month ago has about 13% weight. This creates a "rolling window" of preference that naturally adapts.

**Why 14 Days?** This is a tunable parameter. Too short (3 days) would create volatile recommendations that swing with mood. Too long (90 days) would make the system slow to adapt. 14 days captures genuine preference shifts while filtering out daily mood variation.

**Seasonal Consideration:** You might eventually want longer decay for some signals. If someone consistently saves winter coats every November, that's a seasonal pattern worth remembering even if it's 11 months old.

---

## 6. Perceptual Hashing — The Deduplication Layer

### The Problem It Solves

When aggregating products from multiple partner stores, you'll encounter duplicates:
- Same product sold by different retailers
- Same image used by resellers
- Slight variations (different backgrounds, crops) of the same item
- Products from the same wholesaler appearing in multiple stores

Without deduplication, users see the same item repeatedly, creating a poor experience and wasting valuable feed real estate.

### How Perceptual Hashing Works

Unlike cryptographic hashes (like MD5) that change completely with any tiny modification, perceptual hashes are designed to be similar for visually similar images.

**The Process:**
1. Resize image to small standard size (e.g., 8x8 pixels)
2. Convert to grayscale
3. Compute discrete cosine transform (DCT)
4. Generate hash based on frequency patterns

**The Result:** Two photos of the same item—even with different backgrounds, lighting, or slight crops—will have nearly identical hashes.

### Hamming Distance Threshold

Hamming distance counts how many bits differ between two hashes. Two identical images have distance 0. Completely different images have distance around 32 (for a 64-bit hash).

**Threshold of 5:** This means images are considered duplicates if 5 or fewer bits differ. This catches:
- Same image with different compression
- Same image with slight color adjustment
- Same image with small crops or borders

**Why Not Lower?** A threshold of 2-3 might miss legitimate duplicates with minor variations. A threshold of 8-10 might incorrectly flag similar-but-different items as duplicates.

### Affiliate Self-Competition

This is a subtle but important business consideration. If the same product appears from three different affiliate partners, and user clicks all three over time, you might be diluting your conversion rate and annoying the user. Better to show the product once, from the partner most likely to convert (based on price, shipping, trust signals).

---

## 7. Infrastructure & Cost Control — Building for Reality, Not Fantasy

### Storage Architecture

**⚠️ CRITICAL: No Embedding Duplication in MVP**

| Data Type | Storage | Notes |
|-----------|---------|-------|
| Product embeddings | Qdrant ONLY | Never duplicate in Postgres |
| Product metadata | Qdrant payload | Store with embedding |
| User accounts | PostgreSQL | Standard relational data |
| User feedback (swipes) | PostgreSQL | Training data, precious |
| User style snapshots | PostgreSQL | Periodic vector snapshots |
| User upload images | Hetzner S3 | Original + processed |
| Decision logs | PostgreSQL | GDPR audit trail |
| Session cache | Redis | Short TTL |

**Why This Separation:**
- Qdrant optimized for vector similarity search
- PostgreSQL optimized for relational queries and ACID
- Syncing embeddings between two stores is error-prone
- Saves ~40% storage cost in MVP

```python
# services/storage.py
import boto3
from botocore.config import Config

s3_client = boto3.client(
    's3',
    endpoint_url=settings.S3_ENDPOINT,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
    config=Config(signature_version='s3v4'),
    region_name=settings.S3_REGION
)
```

### Synchronous Inference for MVP

The temptation with ML systems is to build elaborate async architectures with message queues, worker pools, and auto-scaling. For MVP with under 100 users, this is massive over-engineering.

**Why Synchronous Works:**
- FashionSigLIP inference on CPU takes about 100-200ms per image
- With a semaphore limiting to 4 concurrent inferences, worst-case user wait is under 1 second
- No queue management, no worker failures, no message serialization
- Debugging is straightforward (one process, one thread, one request)

**The Semaphore Pattern:** This is elegant. Rather than complex orchestration, a simple semaphore ensures you never have more than 4 images being processed simultaneously. If a 5th request comes in, it waits briefly. This prevents CPU overload while keeping the architecture simple.

### When to Add Complexity

The trigger conditions listed are correct:
- **p95 latency > 500ms:** Users are noticeably waiting
- **Concurrent users > 200:** Semaphore contention becomes real
- **Web search enabled:** External API calls benefit from async
- **GPU node introduced:** Different processing model needed
- **Continuous ingestion:** Background work shouldn't block user requests

The key principle: **add infrastructure complexity in response to measured problems, not anticipated ones.**

---

## 8. Feed Ranking Logic — Balancing Relevance and Business

### Deconstructing the Score Formula

**Cosine Similarity to User Vector (65% weight):** This is the core personalization signal. How similar is this product to what we think the user likes? This should dominate the score, which it does at 65%.

**Cluster Prior Score (15% weight):** For new users or sparse preference data, this provides stability. Even if the personal vector is noisy, the cluster assignment provides a baseline of "this user is probably into streetwear." This prevents wild swings in recommendations during early learning.

**Price Affinity Score (10% weight):** Users have budget realities. Showing a $5,000 jacket to a user who has only engaged with items under $100 is wasting their time and your feed space. This gently filters toward affordable ranges.

**Freshness Score (10% weight):** Prevents recommendation staleness. A store might add new inventory that's perfect for a user. Without freshness boost, the user might never see it because older products have more engagement signal. Freshness keeps the feed dynamic.

### Why These Specific Weights?

The weights reflect priorities:
- Personalization is most important (65%)
- Safety nets for cold-start/sparse data (15% cluster)
- Practical constraints (10% price)
- Discovery and novelty (10% freshness)

These should be tunable parameters, not hardcoded values. A/B testing might reveal that 70/10/10/10 performs better, or that price sensitivity matters more in certain markets.

### Potential Refinements

**Diversity Injection (REQUIRED for MVP):** Without it, echo chambers happen fast. Users get bored seeing the same style repeatedly.

```python
# apps/backend/src/features/feed/service.py
def inject_diversity(ranked_products: list[Product], user_clusters: list[int]) -> list[Product]:
    """
    In every batch of 20, force 2-3 items from adjacent clusters.
    Prevents echo chamber while maintaining relevance.
    """
    BATCH_SIZE = 20
    DIVERSITY_COUNT = 3
    
    result = []
    for i in range(0, len(ranked_products), BATCH_SIZE):
        batch = ranked_products[i:i + BATCH_SIZE]
        
        # Take top items from primary ranking
        primary_items = [p for p in batch if p.cluster_id in user_clusters][:BATCH_SIZE - DIVERSITY_COUNT]
        
        # Add items from adjacent/different clusters
        adjacent_items = [p for p in batch if p.cluster_id not in user_clusters][:DIVERSITY_COUNT]
        
        # Interleave: place diversity items at positions 5, 12, 18
        diversity_positions = [5, 12, 18]
        merged = primary_items.copy()
        for pos, item in zip(diversity_positions, adjacent_items):
            if pos < len(merged):
                merged.insert(pos, item)
            else:
                merged.append(item)
        
        result.extend(merged)
    
    return result
```

**Position Bias Correction:** Items shown first get more engagement regardless of true preference. Consider correcting for position when learning from swipes.

---

## 9. Price Sensitivity Profile — Understanding Budget Reality

### Why This Feature Matters

Fashion apps often fail by ignoring economic reality. A perfect style match that costs 10x the user's budget is useless. Worse, showing unaffordable items repeatedly makes users feel the app "isn't for them."

**Conversion Funnel Impact:** The path from swipe → save → click → purchase has drop-off at each stage. Price mismatch causes massive drop-off at the click → purchase stage, wasting all the engagement that came before.

### The Four Price Metrics

**Preferred Min/Max:** Explicit or inferred boundaries. If a user consistently ignores items below $30 (too cheap, perceived as low quality) or above $200 (too expensive), these become implicit bounds.

**Median Clicked Price:** What price range triggers enough interest to leave the app and visit the store? This is a strong intent signal.

**Median Saved Price:** What price range is worth remembering? Users save items they're seriously considering.

**Why All Four?** They capture different aspects of price sensitivity:
- Bounds define hard limits
- Clicked median shows browsing behavior
- Saved median shows purchase intent

A user might browse (click) more expensive items aspirationally but save more affordable items they might actually buy.

### Nightly Updates

Batch processing makes sense here because:
- Price preferences don't change moment-to-moment
- Calculating across all history is expensive
- Nightly jobs run during low-traffic periods
- Fresh-enough for next-day recommendations

---

## 10. Explainability Layer — Building Trust Through Transparency

### The Psychology of Recommendations

Users are increasingly skeptical of algorithmic recommendations. "Why is this showing me this?" is a common mental question. Without explanation, users might assume:
- Random selection (algorithm is dumb)
- Paid placement (algorithm is corrupt)
- Manipulation (algorithm is trying to sell me something)

Explainability counters all three by showing logical reasoning.

### ⚠️ MVP Explainability: Templates Only

**Do NOT attempt category labeling or semantic explanations in MVP.** This is harder than it looks and will delay launch.

**MVP Implementation: 3 Templates Only**

```typescript
type ExplainabilityTag = 
  | 'similar_to_likes'      // "Similar to your recent likes"
  | 'style_cluster'         // "Matches your style"
  | 'price_match';          // "Within your usual price range"

function getExplanation(product: RankedProduct): ExplainabilityTag {
  // Pick the dominant signal
  if (product.priceScore > 0.8) return 'price_match';
  if (product.clusterScore > product.similarityScore) return 'style_cluster';
  return 'similar_to_likes';
}
```

**Display Strings (with Hebrew):**
```typescript
const explanationStrings: Record<ExplainabilityTag, { en: string; he: string }> = {
  similar_to_likes: { 
    en: "Similar to your recent likes", 
    he: "דומה לפריטים שאהבת" 
  },
  style_cluster: { 
    en: "Matches your style", 
    he: "מתאים לסגנון שלך" 
  },
  price_match: { 
    en: "Within your usual price range", 
    he: "בטווח המחירים שלך" 
  },
};
```

### What NOT to Do in MVP

❌ "Similar to your saved sneakers" — Requires category taxonomy  
❌ "Because you liked the blue jacket" — Requires item-to-item attribution  
❌ "Trending in your area" — Requires geo + trend data  
❌ "Popular with similar users" — Requires collaborative filtering  

### Phase 2 Enhancements

Once MVP is stable, add:
- Category-based explanations (requires product taxonomy)
- Item-to-item references (requires attribution tracking)
- A/B test explanation styles for engagement impact

---

## 11. Business & Monetization — Building for Revenue

### Brand Intelligence as B2B Asset

The schema addition of `brand_id` is forward-thinking. Initially, it's just a data field. Eventually, it enables:

**Brand Dashboards:** "Your products were shown 50,000 times, saved 3,000 times, clicked 500 times." This is valuable information brands will pay for.

**Trend Analysis:** "Minimalist styles are up 30% this month among 18-24 year olds." Sell trend reports to brands and retailers.

**Sponsored Discovery:** Brands pay to boost their products' ranking score slightly. Done carefully, this doesn't harm user experience (only boost relevant items) while generating significant revenue.

### Affiliate Optimization Strategy

**Expected Commission Score:** Not all affiliates pay equally. A $50 item with 10% commission is worth more than a $100 item with 3% commission in absolute terms. Including commission in ranking (gently) maximizes revenue without changing user experience much.

**Conversion Probability:** This is a future ML model that predicts likelihood of purchase based on:
- User's historical conversion rate
- Product category conversion rates
- Price point vs. user's typical purchases
- Time of day/week patterns

Multiplying similarity by conversion probability means you prioritize items the user likes AND is likely to actually buy.

### Ethical Considerations

There's tension between "show what's best for the user" and "show what's best for revenue." The plan handles this well by keeping style relevance as the dominant signal (65%) and treating business optimization as secondary factors.

Transparency matters: if users feel manipulated, they'll leave. Trust is the foundation of recommendation systems.

---

## 12. Compliance & Safety — Protecting Users and Business

### Why Decision Logging Matters

**GDPR Article 22:** Users have the right to not be subject to purely automated decisions, and to receive meaningful information about the logic involved. Decision logs enable you to explain why any specific recommendation was shown.

**Debugging:** When a user reports "why did you show me this weird item?", you can look up exactly what signals contributed to that decision.

**Model Validation:** Comparing decision logs with outcomes (did the user like the recommendation?) helps validate and improve your ranking model.

### What to Log

The schema captures essential signals:
- User and product identifiers (what was shown to whom)
- Similarity score (core ML signal)
- Cluster ID (cold-start factor)
- Price score (practical constraint)
- Timestamp (for temporal analysis)

**What's Missing:** Consider adding:
- Position in feed (for position bias analysis)
- User action (swipe direction, time spent viewing)
- Explanation shown (if any)

### Data Retention Considerations

Decision logs can grow large. Consider:
- 90-day retention for full detail
- Aggregated statistics kept longer
- User deletion requests must purge their logs (GDPR right to erasure)

---

## 13. Custom Swipe Component

Instead of using react-tinder-card, build a custom swipe component using framer-motion for full control:

```tsx
// apps/web/src/features/feed/components/swipe/useSwipeGesture.ts
import { useState, useRef, useCallback } from 'react';
import { useMotionValue, useTransform, PanInfo } from 'framer-motion';

interface SwipeConfig {
  threshold?: number;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
}

export function useSwipeGesture(config: SwipeConfig = {}) {
  const { threshold = 100, onSwipeLeft, onSwipeRight, onSwipeUp } = config;
  
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  
  const rotate = useTransform(x, [-200, 200], [-25, 25]);
  const opacity = useTransform(
    x,
    [-200, -100, 0, 100, 200],
    [0.5, 1, 1, 1, 0.5]
  );
  
  // Visual indicators
  const likeOpacity = useTransform(x, [0, threshold], [0, 1]);
  const nopeOpacity = useTransform(x, [-threshold, 0], [1, 0]);
  const saveOpacity = useTransform(y, [-threshold, 0], [1, 0]);
  
  const handleDragEnd = useCallback(
    (_: never, info: PanInfo) => {
      const { offset } = info;
      
      if (offset.y < -threshold && Math.abs(offset.x) < threshold / 2) {
        // Swipe up - Save
        onSwipeUp?.();
      } else if (offset.x > threshold) {
        // Swipe right - Like
        onSwipeRight?.();
      } else if (offset.x < -threshold) {
        // Swipe left - Nope
        onSwipeLeft?.();
      }
    },
    [threshold, onSwipeLeft, onSwipeRight, onSwipeUp]
  );

  return {
    x,
    y,
    rotate,
    opacity,
    likeOpacity,
    nopeOpacity,
    saveOpacity,
    handleDragEnd,
  };
}
```

```tsx
// apps/web/src/features/feed/components/swipe/SwipeCard.tsx
import { motion } from 'framer-motion';
import { Box, Typography, Chip } from '@mui/material';
import { useSwipeGesture } from './useSwipeGesture';
import type { Product } from '@shared/types';

interface SwipeCardProps {
  product: Product;
  onSwipeLeft: () => void;
  onSwipeRight: () => void;
  onSwipeUp: () => void;
}

export function SwipeCard({ product, onSwipeLeft, onSwipeRight, onSwipeUp }: SwipeCardProps) {
  const {
    x,
    y,
    rotate,
    opacity,
    likeOpacity,
    nopeOpacity,
    saveOpacity,
    handleDragEnd,
  } = useSwipeGesture({
    threshold: 100,
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
  });

  return (
    <motion.div
      style={{
        x,
        y,
        rotate,
        opacity,
        position: 'absolute',
        width: '100%',
        height: '100%',
        cursor: 'grab',
      }}
      drag
      dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
      dragElastic={1}
      onDragEnd={handleDragEnd}
      whileTap={{ cursor: 'grabbing' }}
    >
      <Box
        sx={{
          height: '100%',
          borderRadius: 4,
          overflow: 'hidden',
          boxShadow: 3,
          bgcolor: 'background.paper',
          position: 'relative',
        }}
      >
        {/* Like indicator */}
        <motion.div style={{ opacity: likeOpacity }}>
          <Chip
            label="LIKE"
            color="success"
            sx={{
              position: 'absolute',
              top: 20,
              left: 20,
              fontSize: '1.5rem',
              fontWeight: 'bold',
            }}
          />
        </motion.div>

        {/* Nope indicator */}
        <motion.div style={{ opacity: nopeOpacity }}>
          <Chip
            label="NOPE"
            color="error"
            sx={{
              position: 'absolute',
              top: 20,
              right: 20,
              fontSize: '1.5rem',
              fontWeight: 'bold',
            }}
          />
        </motion.div>

        {/* Save indicator */}
        <motion.div style={{ opacity: saveOpacity }}>
          <Chip
            label="SAVE"
            color="primary"
            sx={{
              position: 'absolute',
              top: 20,
              left: '50%',
              transform: 'translateX(-50%)',
              fontSize: '1.5rem',
              fontWeight: 'bold',
            }}
          />
        </motion.div>

        {/* Product image */}
        <Box
          component="img"
          src={product.imageUrl}
          alt={product.title}
          sx={{
            width: '100%',
            height: '80%',
            objectFit: 'cover',
          }}
        />

        {/* Product info */}
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" noWrap>
            {product.title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            ${product.price} · {product.storeName}
          </Typography>
        </Box>
      </Box>
    </motion.div>
  );
}
```

---

## 14. Infrastructure Configuration

### Docker Compose (Unified)

```yaml
# infra/docker-compose.yml
version: '3.8'

services:
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: stylipp-tunnel
    restart: always
    command: tunnel --no-autoupdate run
    environment:
      - TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}
    networks:
      - stylipp-network

  traefik:
    image: traefik:v3.0
    container_name: stylipp-traefik
    restart: always
    command:
      - "--api.dashboard=false"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--log.level=INFO"
    ports:
      - "80:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - stylipp-network

  web:
    build:
      context: ../apps/web
      dockerfile: Dockerfile
    container_name: stylipp-web
    restart: always
    environment:
      - VITE_API_URL=/api
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=Host(`${DOMAIN}`)"
      - "traefik.http.routers.web.entrypoints=web"
      - "traefik.http.services.web.loadbalancer.server.port=80"
    depends_on:
      - backend
    networks:
      - stylipp-network

  backend:
    build:
      context: ../apps/backend
      dockerfile: Dockerfile
    container_name: stylipp-backend
    restart: always
    environment:
      - DATABASE_URL=postgresql+asyncpg://stylist:${DB_PASSWORD}@postgres:5432/ai_stylist
      - REDIS_URL=redis://redis:6379
      - QDRANT_URL=http://qdrant:6333
      - S3_ENDPOINT=${S3_ENDPOINT}
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - S3_BUCKET=${S3_BUCKET}
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`${DOMAIN}`) && PathPrefix(`/api`)"
      - "traefik.http.routers.api.entrypoints=web"
      - "traefik.http.services.api.loadbalancer.server.port=8000"
      - "traefik.http.middlewares.api-strip.stripprefix.prefixes=/api"
      - "traefik.http.routers.api.middlewares=api-strip"
    depends_on:
      - postgres
      - redis
      - qdrant
    networks:
      - stylipp-network

  postgres:
    image: postgres:16-alpine
    container_name: stylipp-postgres
    restart: always
    environment:
      POSTGRES_USER: stylist
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ai_stylist
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - stylipp-network

  redis:
    image: redis:7-alpine
    container_name: stylipp-redis
    restart: always
    ports:
      - "6379:6379"
    networks:
      - stylipp-network

  qdrant:
    image: qdrant/qdrant:latest
    container_name: stylipp-qdrant
    restart: always
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"
    networks:
      - stylipp-network

volumes:
  postgres_data:
  qdrant_data:

networks:
  stylipp-network:
    driver: bridge
```

---

## 15. CI/CD & Git Hooks

### Husky Configuration

```json
// package.json (root)
{
  "name": "stylipp",
  "private": true,
  "scripts": {
    "dev": "pnpm -r --parallel dev",
    "build": "pnpm -r build",
    "lint": "pnpm -r lint",
    "test": "pnpm -r test",
    "prepare": "husky"
  },
  "devDependencies": {
    "husky": "^9.1.7",
    "lint-staged": "^16.2.7"
  },
  "lint-staged": {
    "apps/web/src/**/*.{ts,tsx}": [
      "pnpm --filter web lint",
      "pnpm --filter web test -- --run"
    ],
    "apps/backend/**/*.py": [
      "pnpm --filter backend lint",
      "pnpm --filter backend test"
    ]
  }
}
```

```bash
# .husky/pre-commit
pnpm lint-staged

# .husky/pre-push
pnpm test
```

### GitHub Actions CI/CD

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v3
        with:
          version: 9
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'pnpm'
      - run: pnpm install
      - run: pnpm --filter web lint
      - run: pnpm --filter web test

  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r apps/backend/requirements.txt
      - run: cd apps/backend && pytest
```

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to server
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/stylipp
            git pull origin main
            docker compose -f infra/docker-compose.prod.yml up -d --build
```

---

## 15.5. Analytics Taxonomy — Instrument from Day One

### Why This Cannot Wait

You will need this data immediately to:
- Debug why recommendations aren't working
- Understand onboarding drop-off points
- Validate ranking weights
- Identify engagement patterns

Retrofitting analytics is painful. Instrument now.

### MVP Event Schema

```typescript
// packages/shared/src/types/analytics.ts

interface BaseEvent {
  event_id: string;          // UUID
  session_id: string;        // UUID, persists across app opens
  user_id: string | null;    // null if not logged in
  timestamp: string;         // ISO 8601
  platform: 'web' | 'ios' | 'android';
  app_version: string;
}

interface FeedViewEvent extends BaseEvent {
  event_type: 'feed_view';
  feed_id: string;           // UUID for this feed request
  products_shown: string[];  // Product IDs in order
}

interface SwipeEvent extends BaseEvent {
  event_type: 'swipe';
  feed_id: string;
  product_id: string;
  position: number;          // 0-indexed position in feed
  action: 'like' | 'dislike' | 'save';
  time_on_card_ms: number;   // How long they looked before swiping
}

interface ProductClickEvent extends BaseEvent {
  event_type: 'product_click';
  product_id: string;
  source: 'feed' | 'favorites' | 'detail';
  position?: number;
}

interface OnboardingEvent extends BaseEvent {
  event_type: 'onboarding_step';
  step: 'started' | 'photo_1' | 'photo_2' | 'calibration_start' | 'calibration_complete' | 'completed';
  step_duration_ms?: number;
}
```

### Backend Event Storage

```python
# apps/backend/src/models/analytics.py
from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    
    # Composite index for common queries
    __table_args__ = (
        Index('ix_analytics_user_type_time', 'user_id', 'event_type', 'timestamp'),
    )
```

### Key Metrics to Track (MVP)

| Metric | Query | Target |
|--------|-------|--------|
| Onboarding completion | `onboarding_step = 'completed' / 'started'` | > 60% |
| D1 retention | Users with session > 24h after signup | > 40% |
| D7 retention | Users with session > 7d after signup | > 20% |
| Swipe-to-save ratio | `save` actions / total swipes | 10-15% |
| Avg time on card | Mean `time_on_card_ms` | 2-4 seconds |
| Feed depth | Avg position of last swipe per session | > 15 |

### Frontend Implementation

```typescript
// apps/web/src/lib/analytics.ts
class Analytics {
  private sessionId: string;
  private queue: BaseEvent[] = [];
  
  constructor() {
    this.sessionId = this.getOrCreateSessionId();
  }
  
  track(event: Omit<BaseEvent, 'event_id' | 'session_id' | 'timestamp'>) {
    const fullEvent: BaseEvent = {
      ...event,
      event_id: crypto.randomUUID(),
      session_id: this.sessionId,
      timestamp: new Date().toISOString(),
    };
    
    this.queue.push(fullEvent);
    this.flush();
  }
  
  private async flush() {
    if (this.queue.length === 0) return;
    
    const events = [...this.queue];
    this.queue = [];
    
    try {
      await fetch('/api/analytics/batch', {
        method: 'POST',
        body: JSON.stringify({ events }),
      });
    } catch (e) {
      // Re-queue on failure
      this.queue.unshift(...events);
    }
  }
}

export const analytics = new Analytics();
```

---

## 16. Execution Roadmap — Reality Check

### Week-by-Week Feasibility

**Week 1 (Foundation):** Product ingestion and embedding generation is achievable in a week if you have partner stores ready. Clustering is a one-time job that can run overnight.

**Week 2 (Core API):** Feed API with ranking logic is the critical path. This needs to be solid before moving on.

**Week 3 (User Interaction):** Swipe UI is straightforward. Feedback pipeline is where errors tend to hide—test thoroughly.

**Week 4 (Monetization):** Affiliate tracking must work correctly. Test with real transactions before launch.

**Week 5 (Polish):** Deduplication and caching are optimizations. Monitoring setup is often underestimated—allocate sufficient time.

**Week 6 (Launch):** "UX polish" can expand infinitely. Timebox this. 50-100 user soft launch is appropriate for initial validation.

### Risks to This Timeline

**Partner Onboarding:** The plan assumes partner stores are ready for integration. If partner negotiations or technical integrations are pending, this blocks Week 1.

**Model Performance:** If FashionSigLIP embeddings don't perform well on your specific inventory (certain fashion niches, quality of product images), you might need additional preprocessing or fine-tuning.

**Testing Depth:** Six weeks is tight for thorough testing. Consider whether a 7th week for bug fixes would reduce launch risk.

---

## 17. Summary of Changes (v1 → v2.1)

| Change | Before (v1) | After (v2.1) |
|--------|-------------|------------|
| **Face Recognition** | Included | ❌ Removed |
| **Person Detection** | YOLOv8 (AGPL) | ❌ MVP: Skip entirely, Phase 2: RT-DETR (Apache) |
| **Onboarding** | 3 photos + 50 swipes | 2 photos + 15 swipes |
| **Cold Start** | Wait for swipes | Cluster-based bootstrap |
| **User Vector** | Simple average | Weighted (positive - negative) |
| **Product Embeddings** | Qdrant + PostgreSQL | Qdrant ONLY (no duplication) |
| **pgvector** | Deferred | Not used in MVP |
| **Redis** | Cache + Queue | Cache ONLY (ARQ disabled) |
| **Task Queue (ARQ)** | Active | ⏸️ Disabled in MVP |
| **Deduplication** | None | Perceptual hashing |
| **Price Profile** | None | Track & use in ranking |
| **Ranking** | Single factor | Multi-factor (4 weights) |
| **Diversity Injection** | None | ✅ 3 items per 20 from adjacent clusters |
| **Explainability** | Category-based | 3 simple templates only |
| **Image Quality Gate** | None | ✅ Blur/size/dimension checks |
| **Analytics** | None | ✅ Full event taxonomy |
| **Partner Fallback** | None | ✅ Bootstrap store (300-500 products) |
| **Audit Trail** | None | GDPR decision logs |
| **Frontend** | Next.js + Tailwind | Vite + React + MUI |
| **Swipe Library** | react-tinder-card | Custom (framer-motion) |
| **Object Storage** | MinIO | Hetzner Object Storage |
| **Architecture** | Flat | Feature-based monorepo |
| **Reverse Proxy** | nginx | Traefik + Cloudflare Tunnel |
| **Search** | Included | Phase 2 (not MVP) |
| **All AI Models** | Mixed licenses | ✅ Apache 2.0 / MIT only (no AGPL) |

---

## 18. Final Assessment — Strengths and Recommendations

### What This Plan Gets Right

**Ruthless Scope Control:** Removing face recognition, search, and person detection saved months of work and legal complexity. This is the hardest decision in product development and you made it correctly.

**AGPL Avoidance:** All models are now Apache 2.0 or MIT licensed. No copyleft risk for your SaaS.

**Cold-Start Innovation:** The clustering approach is elegant and will meaningfully improve first-session experience compared to naive alternatives.

**Infrastructure Pragmatism:** 
- Synchronous inference for MVP (no premature queue complexity)
- Redis for caching only (ARQ disabled until needed)
- No embedding duplication (Qdrant only for products)

**Monetization From Day One:** Affiliate revenue means you can validate business model alongside product-market fit.

**Defense Against Common Failures:**
- ✅ Image quality gate prevents garbage embeddings
- ✅ Diversity injection prevents echo chambers
- ✅ Bootstrap store prevents partner dependency block
- ✅ Analytics from day one enables debugging

### Recommendations for Improvement

**Partner Pipeline:** Even with bootstrap store fallback, start partner conversations now. Real inventory is always better.

**Onboarding A/B Testing:** The 2 photo + 15 swipe requirement is better than before but still might feel like work. Consider testing against 1 photo + 10 swipes to find the minimum viable onboarding.

**Retention Mechanics:** Beyond the core recommendation loop, consider what brings users back. Push notifications for new items matching their style? Weekly style digest emails? These aren't MVP-critical but should be planned.

**Load Testing:** Before soft launch, simulate 50-100 concurrent users to verify semaphore approach holds under real conditions.

### MVP Launch Checklist

- [ ] Bootstrap store populated (300+ products)
- [ ] Image quality gate tested with edge cases
- [ ] Analytics events flowing to database
- [ ] Diversity injection verified in feed
- [ ] Affiliate links working end-to-end
- [ ] Decision logs capturing all required fields
- [ ] Error messages display in Hebrew and English
- [ ] PWA installable on iOS and Android

---

## Conclusion

This is a strong MVP plan that demonstrates startup maturity. The key insight—removing complexity that doesn't directly contribute to core value—is often the difference between shipping and perpetually building.

The clustering-based cold-start solution is particularly clever and will create a meaningfully better first-session experience than most competitors who rely on explicit questionnaires or random exploration.

Execute this plan, get it in front of 100 users, measure everything, and iterate. The plan is good enough; now execution determines success.

---

*Analysis prepared January 2026 — Updated with technical implementation details*
