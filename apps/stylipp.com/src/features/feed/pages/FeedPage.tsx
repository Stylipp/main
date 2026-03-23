import { useRef, useEffect, useCallback } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Skeleton from '@mui/material/Skeleton'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'
import { SwipeCardStack, type SwipeCardStackRef } from '../components/SwipeCardStack'
import { SwipeActions } from '../components/SwipeActions'
import { useFeed } from '../hooks/useFeed'
import { useFeedbackSubmit } from '../hooks/useFeedbackSubmit'
import { useSwipeStore, canUndo as canUndoSelector } from '../stores/swipeStore'

export default function FeedPage() {
  const { currentCard, isLoading, error, refetch } = useFeed()
  const { submitFeedback, undoLastSwipe } = useFeedbackSubmit()
  const userCanUndo = useSwipeStore(canUndoSelector)
  const cards = useSwipeStore((s) => s.cards)
  const reset = useSwipeStore((s) => s.reset)

  const stackRef = useRef<SwipeCardStackRef>(null)

  useEffect(() => {
    return () => reset()
  }, [reset])

  const handleFeedback = useCallback(
    (productId: string, action: 'like' | 'dislike' | 'save') => {
      submitFeedback(productId, action)
    },
    [submitFeedback]
  )

  const handleLike = useCallback(() => {
    stackRef.current?.triggerSwipe('right')
  }, [])

  const handleDislike = useCallback(() => {
    stackRef.current?.triggerSwipe('left')
  }, [])

  const handleSave = useCallback(() => {
    if (currentCard) {
      submitFeedback(currentCard.product_id, 'save')
    }
  }, [currentCard, submitFeedback])

  const isInitialLoad = isLoading && cards.length === 0
  const isFetchingMore = isLoading && cards.length > 0

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100dvh',
        bgcolor: 'background.default',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          py: 1.5,
          position: 'relative',
        }}
      >
        <Typography
          variant="h6"
          sx={{ fontWeight: 700, color: 'primary.main', letterSpacing: '-0.02em' }}
        >
          Stylipp
        </Typography>
        {isFetchingMore && <CircularProgress size={16} sx={{ position: 'absolute', right: 16 }} />}
      </Box>

      {/* Main area */}
      <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {isInitialLoad ? (
          <Box sx={{ position: 'relative', width: '90vw', maxWidth: 400 }}>
            <Skeleton
              variant="rounded"
              sx={{ width: '100%', aspectRatio: '3/4', borderRadius: '16px' }}
            />
            <Skeleton
              variant="rounded"
              sx={{
                width: '90%',
                aspectRatio: '3/4',
                borderRadius: '16px',
                position: 'absolute',
                top: 8,
                left: '5%',
                opacity: 0.5,
              }}
            />
          </Box>
        ) : error && cards.length === 0 ? (
          <Box sx={{ textAlign: 'center', px: 3 }}>
            <ErrorOutlineIcon sx={{ fontSize: 48, color: 'error.main', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Something went wrong
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {error}
            </Typography>
            <Button variant="outlined" onClick={refetch}>
              Try Again
            </Button>
          </Box>
        ) : (
          <SwipeCardStack ref={stackRef} onFeedback={handleFeedback} />
        )}
      </Box>

      {/* Actions */}
      <SwipeActions
        onLike={handleLike}
        onDislike={handleDislike}
        onSave={handleSave}
        onUndo={undoLastSwipe}
        canUndo={userCanUndo}
        disabled={!currentCard}
      />
    </Box>
  )
}
