import { useCallback, useEffect, useRef } from 'react'
import { submitExposureEvents } from '../services/feedbackService'
import type { FeedItem, FeedMode, SwipeAction } from '../types/swipe'

interface ExposureSnapshot {
  shownAt: number
  position: number
}

interface UseExposureTrackingOptions {
  currentCard: FeedItem | null
  currentIndex: number
  feedMode: FeedMode
  sessionId: string
}

export function useExposureTracking({
  currentCard,
  currentIndex,
  feedMode,
  sessionId,
}: UseExposureTrackingOptions) {
  const shownByKey = useRef<Record<string, ExposureSnapshot>>({})
  const sentShownEvents = useRef<Set<string>>(new Set())

  useEffect(() => {
    shownByKey.current = {}
    sentShownEvents.current = new Set()
  }, [sessionId])

  useEffect(() => {
    if (!currentCard) return

    const key = `${sessionId}:${currentCard.product_id}`
    if (sentShownEvents.current.has(key)) return

    const shownAt = Date.now()
    const position = currentIndex + 1
    shownByKey.current[key] = { shownAt, position }
    sentShownEvents.current.add(key)

    void submitExposureEvents([
      {
        product_id: currentCard.product_id,
        session_id: sessionId,
        feed_mode: feedMode,
        position,
        shown_at: new Date(shownAt).toISOString(),
      },
    ]).catch(() => {
      console.warn(`Failed to record exposure for ${currentCard.product_id}`)
    })
  }, [currentCard, currentIndex, feedMode, sessionId])

  const markAction = useCallback(
    (productId: string, action: SwipeAction) => {
      const key = `${sessionId}:${productId}`
      const snapshot = shownByKey.current[key]
      const actionAt = Date.now()

      void submitExposureEvents([
        {
          product_id: productId,
          session_id: sessionId,
          feed_mode: feedMode,
          position: snapshot?.position ?? currentIndex + 1,
          shown_at: new Date(snapshot?.shownAt ?? actionAt).toISOString(),
          action,
          action_at: new Date(actionAt).toISOString(),
          dwell_ms: snapshot ? Math.max(0, actionAt - snapshot.shownAt) : 0,
        },
      ]).catch(() => {
        console.warn(`Failed to update exposure action for ${productId}`)
      })
    },
    [currentIndex, feedMode, sessionId]
  )

  return { markAction }
}
