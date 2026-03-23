import { useEffect, useCallback } from 'react'
import { useSwipeStore } from '../stores/swipeStore'
import { submitFeedback } from '../services/feedbackService'
import type { SwipeAction } from '../types/swipe'

export function useFeedbackSubmit() {
  const addPendingFeedback = useSwipeStore((s) => s.addPendingFeedback)
  const removePendingFeedback = useSwipeStore((s) => s.removePendingFeedback)
  const pendingFeedback = useSwipeStore((s) => s.pendingFeedback)
  const undoLastSwipeStore = useSwipeStore((s) => s.undoLastSwipe)

  const handleSubmitFeedback = useCallback(
    (productId: string, action: SwipeAction) => {
      submitFeedback(productId, action)
        .then(() => {
          // On success: remove from pending queue if it was a retry
          removePendingFeedback(productId)
        })
        .catch(() => {
          // On failure: queue for retry, don't show error to user
          console.warn(`Failed to submit feedback for ${productId}, queuing for retry`)
          addPendingFeedback(productId, action)
        })
    },
    [addPendingFeedback, removePendingFeedback]
  )

  const retryPending = useCallback(() => {
    const pending = useSwipeStore.getState().pendingFeedback
    for (const item of pending) {
      if (item.retryCount >= 3) {
        // Give up silently after 3 retries
        removePendingFeedback(item.productId)
        continue
      }

      // Increment retry count before attempting
      useSwipeStore.setState((state) => ({
        pendingFeedback: state.pendingFeedback.map((pf) =>
          pf.productId === item.productId ? { ...pf, retryCount: pf.retryCount + 1 } : pf
        ),
      }))

      submitFeedback(item.productId, item.action)
        .then(() => {
          removePendingFeedback(item.productId)
        })
        .catch(() => {
          console.warn(`Retry failed for ${item.productId} (attempt ${item.retryCount + 1})`)
        })
    }
  }, [removePendingFeedback])

  const undoLastSwipe = useCallback(() => {
    // Read the top of the undo stack before undoing
    const currentUndoStack = useSwipeStore.getState().undoStack
    if (currentUndoStack.length === 0) return

    const lastRecord = currentUndoStack[0]
    undoLastSwipeStore()

    // Submit corrective feedback — the latest record wins for learning purposes
    if (lastRecord) {
      const oppositeAction: SwipeAction = lastRecord.action === 'like' ? 'dislike' : 'like'
      handleSubmitFeedback(lastRecord.productId, oppositeAction)
    }
  }, [undoLastSwipeStore, handleSubmitFeedback])

  // Auto-retry pending feedback every 30 seconds
  useEffect(() => {
    if (pendingFeedback.length === 0) return

    const interval = setInterval(() => {
      retryPending()
    }, 30_000)

    return () => clearInterval(interval)
  }, [pendingFeedback.length, retryPending])

  return {
    submitFeedback: handleSubmitFeedback,
    retryPending,
    undoLastSwipe,
  }
}
