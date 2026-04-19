import { useEffect, useCallback, useRef, useState } from 'react'
import { useSwipeStore, currentCard, remainingCards } from '../stores/swipeStore'
import { fetchFeed } from '../services/feedbackService'
import type { FeedCategory, FeedItem, FeedMode } from '../types/swipe'

function prefetchImages(cards: FeedItem[], startIndex: number, count: number) {
  for (let i = startIndex; i < Math.min(startIndex + count, cards.length); i++) {
    const img = new Image()
    img.src = cards[i].image_url
  }
}

export function useFeed(category: FeedCategory = 'all') {
  const [feedMode, setFeedMode] = useState<FeedMode>('trending')
  const cards = useSwipeStore((s) => s.cards)
  const current = useSwipeStore(currentCard)
  const remaining = useSwipeStore(remainingCards)
  const isLoading = useSwipeStore((s) => s.isLoading)
  const error = useSwipeStore((s) => s.error)
  const hasMore = useSwipeStore((s) => s.hasMore)
  const nextCursor = useSwipeStore((s) => s.nextCursor)
  const currentIndex = useSwipeStore((s) => s.currentIndex)

  const setCards = useSwipeStore((s) => s.setCards)
  const appendCards = useSwipeStore((s) => s.appendCards)
  const setLoading = useSwipeStore((s) => s.setLoading)
  const setError = useSwipeStore((s) => s.setError)

  const isFetchingMore = useRef(false)
  const loadRequestId = useRef(0)

  const loadInitial = useCallback(async () => {
    const requestId = ++loadRequestId.current
    isFetchingMore.current = false
    setLoading(true)
    setError(null)
    setCards([], null, true)
    try {
      const response = await fetchFeed(undefined, 20, category)
      if (requestId !== loadRequestId.current) return
      setCards(response.items, response.next_cursor, response.has_more)
      setFeedMode(response.feed_mode)
      // Prefetch images for first 3 cards
      prefetchImages(response.items, 0, 3)
    } catch (err) {
      if (requestId !== loadRequestId.current) return
      const message = err instanceof Error ? err.message : 'Failed to load feed'
      setError(message)
      setFeedMode('trending')
    } finally {
      if (requestId === loadRequestId.current) {
        setLoading(false)
      }
    }
  }, [category, setCards, setLoading, setError])

  useEffect(() => {
    void loadInitial()
  }, [loadInitial])

  // Prefetch next page when running low on cards
  useEffect(() => {
    if (remaining <= 5 && hasMore && !isLoading && !isFetchingMore.current && nextCursor) {
      isFetchingMore.current = true
      const requestId = loadRequestId.current
      setLoading(true)
      fetchFeed(nextCursor, 20, category)
        .then((response) => {
          if (requestId !== loadRequestId.current) return
          appendCards(response.items, response.next_cursor, response.has_more)
          setFeedMode(response.feed_mode)
        })
        .catch((err) => {
          if (requestId !== loadRequestId.current) return
          const message = err instanceof Error ? err.message : 'Failed to load more items'
          setError(message)
        })
        .finally(() => {
          if (requestId === loadRequestId.current) {
            setLoading(false)
            isFetchingMore.current = false
          }
        })
    }
  }, [remaining, hasMore, isLoading, nextCursor, appendCards, category, setLoading, setError])

  // Prefetch images for upcoming cards
  useEffect(() => {
    if (cards.length > 0 && currentIndex < cards.length) {
      prefetchImages(cards, currentIndex + 1, 3)
    }
  }, [currentIndex, cards])

  const refetch = useCallback(() => {
    void loadInitial()
  }, [loadInitial])

  return {
    currentCard: current,
    remainingCards: remaining,
    isLoading,
    error,
    hasMore,
    feedMode,
    refetch,
  }
}
