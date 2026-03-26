import Box from '@mui/material/Box'
import { AnimatePresence, motion } from 'framer-motion'
import { useState, useCallback, forwardRef, useImperativeHandle } from 'react'
import { useSwipeStore } from '../stores/swipeStore'
import { SwipeCard } from './SwipeCard'
import type { SwipeDirection, SwipeAction } from '../types/swipe'

export interface SwipeCardStackRef {
  triggerSwipe: (direction: SwipeDirection) => void
}

interface SwipeCardStackProps {
  onFeedback: (productId: string, action: SwipeAction) => void
}

export const SwipeCardStack = forwardRef<SwipeCardStackRef, SwipeCardStackProps>(
  function SwipeCardStack({ onFeedback }, ref) {
    const cards = useSwipeStore((s) => s.cards)
    const currentIndex = useSwipeStore((s) => s.currentIndex)
    const advanceCard = useSwipeStore((s) => s.advanceCard)

    const [exitX, setExitX] = useState(0)

    const visibleCards = cards.slice(currentIndex, currentIndex + 3)

    const handleSwipe = useCallback(
      (direction: SwipeDirection) => {
        const card = cards[currentIndex]
        if (!card) return

        setExitX(direction === 'right' ? 300 : -300)

        const action: SwipeAction = direction === 'right' ? 'like' : 'dislike'
        advanceCard(action)
        onFeedback(card.product_id, action)
      },
      [cards, currentIndex, advanceCard, onFeedback]
    )

    useImperativeHandle(
      ref,
      () => ({
        triggerSwipe: handleSwipe,
      }),
      [handleSwipe]
    )

    return (
      <Box
        sx={{
          position: 'relative',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          width: '100%',
          height: '100%',
          overflow: 'visible',
        }}
      >
        <AnimatePresence>
          {visibleCards.map((card, i) => (
            <motion.div
              key={card.product_id}
              style={{
                position: 'absolute',
                zIndex: 3 - i,
              }}
              initial={{ scale: 0.9, y: 20 }}
              animate={{
                scale: 1 - i * 0.04,
                y: i * 10,
                transition: { type: 'spring', stiffness: 300, damping: 25 },
              }}
              exit={{
                x: exitX,
                opacity: 0,
                rotate: exitX > 0 ? 18 : -18,
                transition: { duration: 0.3, ease: 'easeIn' },
              }}
            >
              <SwipeCard item={card} isTop={i === 0} onSwipe={handleSwipe} exitX={exitX} />
            </motion.div>
          ))}
        </AnimatePresence>
      </Box>
    )
  }
)
