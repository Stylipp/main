import { useRef, useEffect, useCallback, useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Skeleton from '@mui/material/Skeleton'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Snackbar from '@mui/material/Snackbar'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'
import { SwipeCardStack, type SwipeCardStackRef } from '../components/SwipeCardStack'
import { SwipeActions } from '../components/SwipeActions'
import { FeedEmptyState } from '../components/FeedEmptyState'
import { useFeed } from '../hooks/useFeed'
import { useFeedbackSubmit } from '../hooks/useFeedbackSubmit'
import { useSwipeStore, canUndo as canUndoSelector } from '../stores/swipeStore'

export default function FeedPage() {
  const { currentCard, remainingCards, isLoading, error, hasMore, refetch } = useFeed()
  const { submitFeedback, undoLastSwipe } = useFeedbackSubmit()
  const userCanUndo = useSwipeStore(canUndoSelector)
  const cards = useSwipeStore((s) => s.cards)
  const reset = useSwipeStore((s) => s.reset)

  const stackRef = useRef<SwipeCardStackRef>(null)
  const [isAnimating, setIsAnimating] = useState(false)
  const [showSaved, setShowSaved] = useState(false)

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
      setShowSaved(true)
    }
  }, [currentCard, submitFeedback])

  const handleUndo = useCallback(() => {
    if (isAnimating) return
    undoLastSwipe()
    setIsAnimating(true)
    setTimeout(() => setIsAnimating(false), 300)
  }, [isAnimating, undoLastSwipe])

  const isInitialLoad = isLoading && cards.length === 0
  const isFetchingMore = isLoading && cards.length > 0
  const noCards = !isInitialLoad && remainingCards === 0 && !hasMore && !isLoading

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100dvh',
        bgcolor: 'background.default',
        overflow: 'hidden',
        /* Center as a mobile-app shell on desktop */
        maxWidth: 480,
        mx: 'auto',
        width: '100%',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          py: 1.5,
          px: 2,
          position: 'relative',
          flexShrink: 0,
        }}
      >
        <Typography
          variant="h6"
          sx={{
            fontWeight: 700,
            color: 'primary.main',
            letterSpacing: '-0.03em',
            fontSize: '1.35rem',
          }}
        >
          Stylipp
        </Typography>
        {isFetchingMore && (
          <CircularProgress
            size={14}
            thickness={5}
            sx={{ position: 'absolute', right: 20, color: 'primary.light' }}
          />
        )}
      </Box>

      {/* Main card area — takes all remaining space */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: 0,
          px: 2,
        }}
      >
        {isInitialLoad ? (
          <Box sx={{ position: 'relative', width: '100%', maxWidth: 380 }}>
            <Skeleton
              variant="rounded"
              animation="wave"
              sx={{
                width: '100%',
                aspectRatio: '3/4',
                borderRadius: '20px',
              }}
            />
            <Skeleton
              variant="rounded"
              animation="wave"
              sx={{
                width: '92%',
                aspectRatio: '3/4',
                borderRadius: '20px',
                position: 'absolute',
                top: 10,
                left: '4%',
                opacity: 0.4,
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
            <Button variant="outlined" onClick={refetch} sx={{ borderRadius: 12 }}>
              Try Again
            </Button>
          </Box>
        ) : noCards ? (
          <FeedEmptyState onRefresh={refetch} />
        ) : (
          <SwipeCardStack ref={stackRef} onFeedback={handleFeedback} />
        )}
      </Box>

      {/* Actions — fixed at bottom */}
      <Box sx={{ flexShrink: 0 }}>
        <SwipeActions
          onLike={handleLike}
          onDislike={handleDislike}
          onSave={handleSave}
          onUndo={handleUndo}
          canUndo={userCanUndo && !isAnimating}
          disabled={isInitialLoad || (noCards && !userCanUndo)}
        />
      </Box>

      <Snackbar
        open={showSaved}
        autoHideDuration={1500}
        onClose={() => setShowSaved(false)}
        message="Saved!"
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        ContentProps={{
          sx: {
            bgcolor: 'primary.main',
            borderRadius: '12px',
            fontWeight: 600,
            minWidth: 'auto',
          },
        }}
      />
    </Box>
  )
}
