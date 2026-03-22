# Phase 6: Swipe Interface & Feedback - Research

**Researched:** 2026-03-22
**Domain:** Interactive swipe card UI with gesture physics + feedback persistence pipeline
**Confidence:** HIGH

<research_summary>
## Summary

Researched the ecosystem for building a Tinder-style swipe card interface in React 19 with framer-motion, plus backend feedback persistence patterns.

**Key finding:** framer-motion (Motion ^12.30.0, already installed) provides everything needed for production swipe gestures — drag props, velocity/offset detection via `onDragEnd`, spring physics, and `AnimatePresence` for exit animations. **Do not add `react-tinder-card`** — it depends on `@react-spring/web` which has unresolved React 19 compatibility issues (peer dep `^16.8.0 || ^17.0.0 || ^18.0.0`). Building with native Motion APIs avoids the dependency conflict and gives full control over gesture physics and animation.

The standard approach: `useMotionValue` tracks drag position, `useTransform` derives rotation/opacity/indicator visibility, `onDragEnd` checks `info.offset.x` and `info.velocity.x` against thresholds to determine swipe direction, then `AnimatePresence` + `exit` prop animates the card off-screen. Card stack renders only top 2-3 cards for performance.

**Primary recommendation:** Use Motion's native drag API (already installed). Render 2-3 card stack with `AnimatePresence`. Threshold: `|offset.x| > 100px OR |velocity.x| > 500px/s`. Optimistic UI for feedback submission. New `user_interactions` table for persistence.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| motion (framer-motion) | ^12.30.0 | Drag gestures, spring animations, exit animations | Already installed. Industry-standard React animation library (30k+ GitHub stars). Native drag API with velocity/offset detection |
| React 19 | ^19.2.0 | UI framework | Already installed. AnimatePresence works with React 19 |
| @mui/material | ^7.3.7 | Card UI, icons, buttons | Already installed. Consistent with existing design system |
| zustand | ^5.0.11 | Swipe state, feedback queue | Already installed. Lightweight, perfect for card stack state |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none needed) | - | - | All dependencies already present |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Motion drag API | react-tinder-card | **AVOID** — depends on @react-spring/web which lacks React 19 support. Would require `--legacy-peer-deps` hack |
| Motion drag API | @use-gesture/react + react-spring | Overkill — Motion already handles gestures natively. Same React 19 issue with react-spring |
| Motion drag API | react-swipeable | Only detects swipe direction — no animation, no physics. Would need to pair with Motion anyway |
| Custom swipe component | Embla Carousel (installed) | Carousel is for sequential browsing, not Tinder-style accept/reject |

**Installation:**
```bash
# No new dependencies needed — everything is already installed
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Component Structure
```
src/features/feed/
├── components/
│   ├── SwipeCard.tsx          # Single draggable card with gesture physics
│   ├── SwipeCardStack.tsx     # Stack manager (renders top 2-3 cards)
│   ├── SwipeIndicators.tsx    # Like/Dislike/Save overlays driven by drag position
│   └── SwipeActions.tsx       # Button controls (like, dislike, save, undo)
├── hooks/
│   ├── useSwipeGesture.ts     # Encapsulates drag threshold logic
│   └── useFeedbackSubmit.ts   # Optimistic feedback API calls
├── stores/
│   └── swipeStore.ts          # Card queue, current index, undo stack
├── services/
│   └── feedbackService.ts     # API client for POST /api/feedback
└── types/
    └── swipe.ts               # SwipeDirection, SwipeAction types
```

### Pattern 1: Motion Drag with Threshold Detection
**What:** Use `useMotionValue` to track drag position, `onDragEnd` to detect swipe vs cancel
**When to use:** Every swipeable card
**Example:**
```typescript
// Source: Motion docs (motion.dev/docs/react-drag) + community patterns
import { motion, useMotionValue, useTransform, AnimatePresence } from 'motion/react'

const SWIPE_THRESHOLD = 100    // pixels offset
const VELOCITY_THRESHOLD = 500 // pixels/second

function SwipeCard({ item, onSwipe, isTop }: SwipeCardProps) {
  const x = useMotionValue(0)
  const rotate = useTransform(x, [-200, 200], [-15, 15])
  const likeOpacity = useTransform(x, [0, 100], [0, 1])
  const dislikeOpacity = useTransform(x, [-100, 0], [1, 0])

  const handleDragEnd = (event: PointerEvent, info: PanInfo) => {
    const { offset, velocity } = info
    if (Math.abs(offset.x) > SWIPE_THRESHOLD || Math.abs(velocity.x) > VELOCITY_THRESHOLD) {
      const direction = offset.x > 0 ? 'right' : 'left'
      onSwipe(direction)
    }
    // If thresholds not met, dragSnapToOrigin returns card to center
  }

  return (
    <motion.div
      drag={isTop ? 'x' : false}
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={0.7}
      dragSnapToOrigin
      style={{ x, rotate }}
      onDragEnd={handleDragEnd}
      exit={{ x: exitX, opacity: 0, transition: { duration: 0.3 } }}
      whileDrag={{ cursor: 'grabbing', scale: 1.02 }}
    >
      {/* Card content */}
      <LikeIndicator style={{ opacity: likeOpacity }} />
      <DislikeIndicator style={{ opacity: dislikeOpacity }} />
    </motion.div>
  )
}
```

### Pattern 2: Card Stack with AnimatePresence
**What:** Render only top 2-3 cards, use AnimatePresence for exit animations
**When to use:** The stack container component
**Example:**
```typescript
// Source: Motion AnimatePresence docs + card stack tutorial
function SwipeCardStack({ items }: { items: FeedItem[] }) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [exitX, setExitX] = useState(0)

  const visibleCards = items.slice(currentIndex, currentIndex + 3)

  const handleSwipe = (direction: 'left' | 'right') => {
    setExitX(direction === 'right' ? 300 : -300)
    setCurrentIndex(prev => prev + 1)
    // Submit feedback
  }

  return (
    <div style={{ position: 'relative' }}>
      <AnimatePresence>
        {visibleCards.map((item, i) => (
          <SwipeCard
            key={item.product_id}
            item={item}
            isTop={i === 0}
            onSwipe={handleSwipe}
            style={{
              position: 'absolute',
              scale: 1 - i * 0.05,
              y: i * 8,
              zIndex: visibleCards.length - i,
            }}
          />
        ))}
      </AnimatePresence>
    </div>
  )
}
```

### Pattern 3: Optimistic Feedback Submission
**What:** Submit feedback immediately without waiting for server response
**When to use:** All like/dislike/save actions
**Example:**
```typescript
// Optimistic: fire-and-forget, queue for retry on failure
function useFeedbackSubmit() {
  const submitFeedback = async (productId: string, action: SwipeAction) => {
    // Update local state immediately (optimistic)
    swipeStore.getState().recordAction(productId, action)

    // Fire API call in background
    try {
      await apiClient.post('/api/feedback', { product_id: productId, action })
    } catch {
      // Queue for retry — don't block the UI
      swipeStore.getState().queueRetry(productId, action)
    }
  }
  return { submitFeedback }
}
```

### Anti-Patterns to Avoid
- **Rendering all cards in the stack:** Only render top 2-3. More causes layout thrashing and wasted memory
- **Using state for drag position:** Use `useMotionValue` — it doesn't trigger re-renders during drag
- **Blocking UI on feedback API calls:** Use optimistic updates — swipe must feel instant
- **Animating with CSS transitions instead of Motion:** Loss of spring physics, velocity-based momentum, and gesture continuity
- **Using dragConstraints to limit movement:** Use `dragSnapToOrigin` instead — let users drag freely, then snap back if below threshold
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Drag gesture detection | Custom touch/pointer event handlers | Motion `drag` prop | Handles pointer, touch, and mouse events uniformly. Provides velocity, offset, direction lock |
| Spring physics on snap-back | Manual easing/timing functions | Motion `dragSnapToOrigin` + `dragTransition` | Physical spring model feels natural. Custom easing never matches |
| Exit animations | Manual DOM removal with setTimeout | `AnimatePresence` + `exit` prop | Handles unmount delay, interruptible animations, layout recalculation |
| Rotation during drag | Manual transform calculation | `useTransform(x, inputRange, outputRange)` | Reactive, no re-renders, automatically interpolates |
| Velocity-based swipe detection | Manual velocity calculation from touch events | Motion `onDragEnd` `info.velocity` | Already computed by Motion's gesture engine at 60fps |
| Card stacking visual | Manual z-index/transform management | `motion.div` with dynamic `style` prop | Animates between stack positions automatically |
| Scroll vs drag conflict | Custom touch-action logic | CSS `touch-action: none` on drag element | Browser-native, no JS overhead, works on all mobile browsers |

**Key insight:** Motion's drag system is a complete gesture engine — it tracks pointer position, calculates velocity, handles inertia, provides spring physics, and manages animation lifecycle. Every manual reimplementation of any part of this will be buggier and less performant.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Scroll vs Swipe Conflict on Mobile
**What goes wrong:** Horizontal swipe on card triggers vertical page scroll, or vice versa
**Why it happens:** Browser touch handling conflicts with gesture handlers
**How to avoid:** Set `touch-action: none` CSS on the draggable card element. Use `drag="x"` to lock to horizontal axis. Motion automatically handles this when `drag` is set, but explicit CSS prevents edge cases
**Warning signs:** Jerky behavior on mobile, card "sticking" during swipe, page scrolling when swiping

### Pitfall 2: Re-renders During Drag Kill Performance
**What goes wrong:** Card stutters/lags during drag, especially on low-end mobile
**Why it happens:** Using React state (`useState`) to track drag position causes re-renders on every frame
**How to avoid:** Always use `useMotionValue` for drag-coupled values. Use `useTransform` for derived values (rotation, opacity). These bypass React's render cycle entirely
**Warning signs:** React DevTools showing renders during drag, requestAnimationFrame drops, lag between finger and card position

### Pitfall 3: Card Stack Memory Leak
**What goes wrong:** App slows down after many swipes, memory usage grows
**Why it happens:** Keeping all swiped cards in state/DOM, accumulating event listeners
**How to avoid:** Remove cards from array after exit animation completes (use `onAnimationComplete` or the `AnimatePresence` `onExitComplete` callback). Only keep last N cards in undo stack (e.g., 5)
**Warning signs:** DOM node count growing, increasing memory in DevTools, AnimatePresence children list growing

### Pitfall 4: Exit Animation Direction Wrong
**What goes wrong:** Card exits left when swiped right, or always exits same direction
**Why it happens:** `exit` prop is static — it doesn't know which direction the user swiped
**How to avoid:** Store exit direction in state before removing card. Use dynamic `exit` based on a `custom` prop or state variable. Set `exitX` in `onDragEnd` handler BEFORE updating the card index
**Warning signs:** Card animation feels disconnected from gesture, cards always fly same direction

### Pitfall 5: Buttons Inside Cards Don't Work
**What goes wrong:** Tapping "Save" or product link inside card triggers drag instead
**Why it happens:** Motion's drag listener captures all pointer events on the element
**How to avoid:** Use `dragListener={false}` on the card and `useDragControls` to initiate drag from a specific handle area. OR use `onPointerDownCapture` with `e.stopPropagation()` on interactive elements. OR use separate drag overlay on top of card content
**Warning signs:** Buttons unresponsive, links don't navigate, any tap starts a drag

### Pitfall 6: Feed Runs Out of Cards
**What goes wrong:** User sees empty state, no cards left
**Why it happens:** Feed batch consumed before next batch fetched
**How to avoid:** Prefetch next batch when current batch reaches 5 remaining cards. Use the feed's cursor-based pagination (`next_cursor` from Phase 5). Show skeleton cards while loading
**Warning signs:** Flicker to empty state, loading spinner between batches
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from official sources:

### Motion Drag with Velocity Detection
```typescript
// Source: motion.dev/docs/react-drag + community patterns
import { motion, type PanInfo } from 'motion/react'

// onDragEnd receives info object with offset and velocity
const handleDragEnd = (_event: PointerEvent, info: PanInfo) => {
  // info.offset  — { x: number, y: number } — total distance from start
  // info.velocity — { x: number, y: number } — current velocity in px/s
  // info.point   — { x: number, y: number } — current pointer coordinates

  const swipedRight = info.offset.x > 100 || info.velocity.x > 500
  const swipedLeft  = info.offset.x < -100 || info.velocity.x < -500

  if (swipedRight) onSwipe('right')  // LIKE
  else if (swipedLeft) onSwipe('left') // DISLIKE
  // else: dragSnapToOrigin returns card to center
}

<motion.div
  drag="x"
  dragSnapToOrigin     // Returns to center if not swiped
  dragElastic={0.7}    // Resistance feel (0 = rigid, 1 = no resistance)
  dragTransition={{    // Customize snap-back spring
    bounceStiffness: 300,
    bounceDamping: 20,
  }}
  onDragEnd={handleDragEnd}
  whileDrag={{ scale: 1.02 }}
  style={{ touchAction: 'none' }}  // CRITICAL for mobile
/>
```

### useTransform for Visual Feedback
```typescript
// Source: motion.dev docs — useTransform maps one MotionValue to another
import { useMotionValue, useTransform } from 'motion/react'

function SwipeCard() {
  const x = useMotionValue(0)

  // Rotate card as it's dragged (-15deg to +15deg)
  const rotate = useTransform(x, [-200, 200], [-15, 15])

  // Show LIKE indicator as card moves right
  const likeOpacity = useTransform(x, [0, 100], [0, 1])

  // Show NOPE indicator as card moves left
  const nopeOpacity = useTransform(x, [-100, 0], [1, 0])

  // Background tint (green for like, red for dislike)
  const bgColor = useTransform(
    x,
    [-200, -50, 0, 50, 200],
    ['rgba(239,68,68,0.2)', 'rgba(239,68,68,0)', 'transparent', 'rgba(34,197,94,0)', 'rgba(34,197,94,0.2)']
  )

  return (
    <motion.div style={{ x, rotate, backgroundColor: bgColor }}>
      <motion.div className="like-stamp" style={{ opacity: likeOpacity }}>LIKE</motion.div>
      <motion.div className="nope-stamp" style={{ opacity: nopeOpacity }}>NOPE</motion.div>
    </motion.div>
  )
}
```

### AnimatePresence for Card Exit
```typescript
// Source: motion.dev/docs/react-animate-presence
import { AnimatePresence, motion } from 'motion/react'

function CardStack({ cards, currentIndex }) {
  return (
    <AnimatePresence onExitComplete={() => {/* cleanup swiped card */}}>
      {cards.slice(currentIndex, currentIndex + 3).map((card, i) => (
        <motion.div
          key={card.product_id}  // Unique key required for AnimatePresence
          initial={{ scale: 0.95, y: 10 }}
          animate={{
            scale: 1 - i * 0.05,
            y: i * 8,
            zIndex: 3 - i,
          }}
          exit={{
            x: exitDirection * 300,
            opacity: 0,
            rotate: exitDirection * 20,
            transition: { duration: 0.3 }
          }}
          transition={{ type: 'spring', stiffness: 300, damping: 25 }}
        >
          <ProductCard data={card} />
        </motion.div>
      ))}
    </AnimatePresence>
  )
}
```

### Button Actions (Programmatic Swipe)
```typescript
// Source: Community pattern for accessibility / button-triggered swipes
import { useAnimate } from 'motion/react'

function SwipeActions({ onLike, onDislike, onSave }) {
  const [scope, animate] = useAnimate()

  const triggerSwipe = async (direction: 'left' | 'right') => {
    await animate(scope.current, {
      x: direction === 'right' ? 300 : -300,
      rotate: direction === 'right' ? 20 : -20,
      opacity: 0,
    }, { duration: 0.3 })
    direction === 'right' ? onLike() : onDislike()
  }

  return (
    <div>
      <IconButton onClick={() => triggerSwipe('left')}><CloseIcon /></IconButton>
      <IconButton onClick={onSave}><BookmarkIcon /></IconButton>
      <IconButton onClick={() => triggerSwipe('right')}><FavoriteIcon /></IconButton>
    </div>
  )
}
```

### Backend Feedback Endpoint Pattern
```python
# Source: Standard FastAPI pattern matching existing project conventions
# POST /api/feedback
class FeedbackAction(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    SAVE = "save"

class FeedbackRequest(BaseModel):
    product_id: str
    action: FeedbackAction

class UserInteraction(Base):
    __tablename__ = "user_interactions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), index=True)
    action: Mapped[str]  # 'like', 'dislike', 'save'
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Composite index for "has user interacted with product"
    __table_args__ = (
        Index('ix_user_product', 'user_id', 'product_id'),
        Index('ix_user_action_time', 'user_id', 'action', 'created_at'),
    )
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| framer-motion package name | `motion/react` import path | Motion v11+ (2024) | Import from `motion/react` not `framer-motion` — but `framer-motion` still works as alias |
| react-spring for gesture animations | Motion (framer-motion) native drag | 2023+ | Motion's drag API is now more capable and actively maintained than react-spring |
| react-tinder-card | Custom Motion drag implementation | 2024+ | react-tinder-card stuck on react-spring ^9.5.5, no React 19 support |
| Separate gesture library (@use-gesture) | Motion built-in gestures | Motion v10+ | No need for separate gesture library when using Motion |
| CSS transitions for card animations | Spring-based physics animations | 2022+ | Springs feel more natural, respond to velocity, interruptible |

**New tools/patterns to consider:**
- **`useAnimate` hook (Motion v10+):** Imperative animation API for programmatic swipes (button-triggered)
- **`useMotionValueEvent` hook:** Listen to MotionValue changes without re-renders — perfect for threshold indicators
- **`motion/react` import path:** Newer canonical import, tree-shakeable

**Deprecated/outdated:**
- **react-tinder-card:** Blocked on @react-spring React 19 support. No new releases addressing this
- **@use-gesture/react + react-spring combo:** Was the standard pre-Motion-v10. Motion now handles everything natively
- **Manual requestAnimationFrame for gesture tracking:** Motion's MotionValue system is more efficient and handles frame scheduling internally
</sota_updates>

<open_questions>
## Open Questions

1. **Save action: up-swipe vs button only?**
   - What we know: Tinder uses up-swipe for "super like." The roadmap mentions "save" as distinct from like
   - What's unclear: Whether save should be a gesture (swipe up) or button-only
   - Recommendation: Start with button-only save. Add swipe-up later if users request it. Keeps gesture model simple (left=dislike, right=like)

2. **Undo functionality scope**
   - What we know: Users occasionally swipe wrong direction accidentally
   - What's unclear: How many actions to allow undoing, whether undo requires backend DELETE
   - Recommendation: Keep last 5 actions in local undo stack. Undo sends corrective action to backend (new interaction record, not DELETE). Simple and audit-friendly

3. **Haptic feedback on mobile**
   - What we know: Vibration API (`navigator.vibrate()`) available on Android, limited on iOS Safari
   - What's unclear: Whether iOS PWA supports Vibration API at all (historically blocked)
   - Recommendation: Add haptic as enhancement only (don't depend on it). Check `navigator.vibrate` exists before calling. Visual/audio feedback is primary
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- Motion official drag docs (motion.dev/docs/react-drag) — drag props, dragElastic, dragSnapToOrigin, onDragEnd info object
- Motion AnimatePresence docs (motion.dev/docs/react-animate-presence) — exit animations, key requirements
- Motion gesture docs (motion.dev/docs/react-gestures) — whileDrag, dragDirectionLock, drag="x"

### Secondary (MEDIUM confidence)
- [OlegWock: Drag snap points](https://sinja.io/blog/framer-motion-drag-snap-points) — onDragEnd info.offset/velocity structure, snap implementation, dragElastic exponential decay formula
- [OlegWock: Swipe actions](https://sinja.io/blog/swipe-actions-react-framer-motion) — accessibility patterns (focus/blur), react-use-motion-measure for non-rerender measurements
- [GeeksforGeeks: Tinder swipe with framer-motion](https://www.geeksforgeeks.org/how-to-create-tinder-card-swipe-gesture-using-react-and-framer-motion/) — useMotionValue + useTransform + useAnimation pattern, 150px threshold
- [DEV.to: Tinder-like card game](https://dev.to/lansolo99/a-tinder-like-card-game-with-framer-motion-35i5) — dragSnapToOrigin, overlay indicator pattern, useMotionValueEvent
- [Maxime Heckel: Advanced animation patterns](https://blog.maximeheckel.com/posts/advanced-animation-patterns-with-framer-motion/) — AnimatePresence with layout animations, stack 3D pattern
- [MDN: touch-action CSS](https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action) — mobile scroll/drag conflict prevention

### Tertiary (LOW confidence - needs validation)
- react-tinder-card React 19 incompatibility — verified via GitHub issues (#2341 on react-spring) and npm peer deps. Confirmed: @react-spring/web ^9.5.5 doesn't declare React 19 support
- react-spring v10.0.3 — latest version but React 19 support issue still open as of search date
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Motion (framer-motion) ^12.30.0 drag/gesture API
- Ecosystem: Evaluated react-tinder-card (rejected: React 19 incompatible), react-swipeable (rejected: no animation), @use-gesture (rejected: redundant)
- Patterns: Card stack with AnimatePresence, useMotionValue-driven visual feedback, optimistic feedback submission
- Pitfalls: Mobile scroll conflict, re-render during drag, exit direction, button-in-card, feed exhaustion

**Confidence breakdown:**
- Standard stack: HIGH — already installed, no new dependencies needed
- Architecture: HIGH — patterns from official Motion docs + multiple verified community implementations
- Pitfalls: HIGH — documented in Motion GitHub issues, blog posts, and community examples
- Code examples: HIGH — from Motion official docs, verified against API signatures

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (30 days — Motion ecosystem stable, no breaking changes expected)
</metadata>

---

*Phase: 06-swipe-interface-feedback*
*Research completed: 2026-03-22*
*Ready for planning: yes*
