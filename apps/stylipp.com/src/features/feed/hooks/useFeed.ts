import { useEffect, useCallback, useRef } from 'react'
import { useSwipeStore, currentCard, remainingCards } from '../stores/swipeStore'
import { fetchFeed } from '../services/feedbackService'
import type { FeedItem } from '../types/swipe'

function prefetchImages(cards: FeedItem[], startIndex: number, count: number) {
  for (let i = startIndex; i < Math.min(startIndex + count, cards.length); i++) {
    const img = new Image()
    img.src = cards[i].image_url
  }
}

export function useFeed() {
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

  const mountGuard = useRef(false)
  const isFetchingMore = useRef(false)

  const loadInitial = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetchFeed(undefined, 20)
      setCards(response.items, response.next_cursor, response.has_more)
      // Prefetch images for first 3 cards
      prefetchImages(response.items, 0, 3)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load feed'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [setCards, setLoading, setError])

  // Initial fetch on mount
  useEffect(() => {
    if (!mountGuard.current) {
      mountGuard.current = true
      loadInitial()
    }
  }, [loadInitial])

  // Prefetch next page when running low on cards
  useEffect(() => {
    if (remaining <= 5 && hasMore && !isLoading && !isFetchingMore.current && nextCursor) {
      isFetchingMore.current = true
      setLoading(true)
      fetchFeed(nextCursor, 20)
        .then((response) => {
          appendCards(response.items, response.next_cursor, response.has_more)
        })
        .catch((err) => {
          const message = err instanceof Error ? err.message : 'Failed to load more items'
          setError(message)
        })
        .finally(() => {
          setLoading(false)
          isFetchingMore.current = false
        })
    }
  }, [remaining, hasMore, isLoading, nextCursor, appendCards, setLoading, setError])

  // Prefetch images for upcoming cards
  useEffect(() => {
    if (cards.length > 0 && currentIndex < cards.length) {
      prefetchImages(cards, currentIndex + 1, 3)
    }
  }, [currentIndex, cards])

  const refetch = useCallback(() => {
    mountGuard.current = false
    loadInitial()
  }, [loadInitial])

  return {
    currentCard: current,
    remainingCards: remaining,
    isLoading,
    error,
    hasMore,
    refetch,
  }
}
