import Box from '@mui/material/Box'
import { AnimatePresence, motion } from 'framer-motion'
import { useState, useCallback } from 'react'
import { useSwipeStore } from '../stores/swipeStore'
import { SwipeCard } from './SwipeCard'
import type { SwipeDirection, SwipeAction } from '../types/swipe'

interface SwipeCardStackProps {
  onFeedback: (productId: string, action: SwipeAction) => void
}

export function SwipeCardStack({ onFeedback }: SwipeCardStackProps) {
  const cards = useSwipeStore((s) => s.cards)
  const currentIndex = useSwipeStore((s) => s.currentIndex)
  const advanceCard = useSwipeStore((s) => s.advanceCard)

  const [exitX, setExitX] = useState(0)

  const visibleCards = cards.slice(currentIndex, currentIndex + 3)

  const handleSwipe = useCallback(
    (direction: SwipeDirection) => {
      const card = cards[currentIndex]
      if (!card) return

      // Set exitX BEFORE advanceCard so the exiting card reads the correct direction
      setExitX(direction === 'right' ? 300 : -300)

      const action: SwipeAction = direction === 'right' ? 'like' : 'dislike'
      advanceCard(action)
      onFeedback(card.product_id, action)
    },
    [cards, currentIndex, advanceCard, onFeedback]
  )

  return (
    <Box
      sx={{
        position: 'relative',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: { xs: 480, md: 560 },
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
            initial={{ scale: 0.9, y: 16 }}
            animate={{
              scale: 1 - i * 0.05,
              y: i * 8,
              transition: { type: 'spring', stiffness: 300, damping: 25 },
            }}
            exit={{
              x: exitX,
              opacity: 0,
              rotate: exitX > 0 ? 20 : -20,
              transition: { duration: 0.3 },
            }}
          >
            <SwipeCard item={card} isTop={i === 0} onSwipe={handleSwipe} exitX={exitX} />
          </motion.div>
        ))}
      </AnimatePresence>
    </Box>
  )
}
