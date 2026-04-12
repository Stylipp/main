import { create } from 'zustand'
import type { FeedItem, SwipeRecord, PendingFeedback, SwipeAction } from '../types/swipe'

const MAX_UNDO_STACK = 5

interface SwipeState {
  cards: FeedItem[]
  currentIndex: number
  undoStack: SwipeRecord[]
  pendingFeedback: PendingFeedback[]
  isLoading: boolean
  error: string | null
  nextCursor: string | null
  hasMore: boolean

  setCards: (cards: FeedItem[], nextCursor: string | null, hasMore: boolean) => void
  appendCards: (cards: FeedItem[], nextCursor: string | null, hasMore: boolean) => void
  advanceCard: (action: SwipeAction) => void
  undoLastSwipe: () => void
  addPendingFeedback: (productId: string, action: SwipeAction) => void
  removePendingFeedback: (productId: string) => void
  setLoading: (isLoading: boolean) => void
  setError: (error: string | null) => void
  reset: () => void
}

const initialState = {
  cards: [] as FeedItem[],
  currentIndex: 0,
  undoStack: [] as SwipeRecord[],
  pendingFeedback: [] as PendingFeedback[],
  isLoading: false,
  error: null as string | null,
  nextCursor: null as string | null,
  hasMore: true,
}

export const useSwipeStore = create<SwipeState>()((set) => ({
  ...initialState,

  setCards: (cards, nextCursor, hasMore) =>
    set({ cards, currentIndex: 0, undoStack: [], nextCursor, hasMore }),

  appendCards: (cards, nextCursor, hasMore) =>
    set((state) => ({
      cards: [...state.cards, ...cards],
      nextCursor,
      hasMore,
    })),

  advanceCard: (action) =>
    set((state) => {
      const card = state.cards[state.currentIndex]
      if (!card) return state

      const record: SwipeRecord = {
        productId: card.product_id,
        action,
        timestamp: Date.now(),
      }

      return {
        currentIndex: state.currentIndex + 1,
        undoStack: [record, ...state.undoStack].slice(0, MAX_UNDO_STACK),
      }
    }),

  undoLastSwipe: () =>
    set((state) => {
      if (state.undoStack.length === 0 || state.currentIndex === 0) return state
      return {
        currentIndex: state.currentIndex - 1,
        undoStack: state.undoStack.slice(1),
      }
    }),

  addPendingFeedback: (productId, action) =>
    set((state) => ({
      pendingFeedback: [...state.pendingFeedback, { productId, action, retryCount: 0 }],
    })),

  removePendingFeedback: (productId) =>
    set((state) => ({
      pendingFeedback: state.pendingFeedback.filter((pf) => pf.productId !== productId),
    })),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  reset: () => set(initialState),
}))

// Selectors
export const currentCard = (state: SwipeState): FeedItem | null =>
  state.cards[state.currentIndex] ?? null

export const remainingCards = (state: SwipeState): number => state.cards.length - state.currentIndex

export const canUndo = (state: SwipeState): boolean =>
  state.undoStack.length > 0 && state.currentIndex > 0
