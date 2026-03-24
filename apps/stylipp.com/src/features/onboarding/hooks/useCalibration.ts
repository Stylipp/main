import { useState, useEffect, useCallback, useRef } from 'react'
import api from '@/shared/hooks/useApi'
import { useOnboardingStore } from '@/features/onboarding/stores/onboardingStore'

export interface CalibrationItem {
  product_id: string
  title: string
  price: number
  currency: string
  image_url: string
}

interface UseCalibrationReturn {
  items: CalibrationItem[]
  currentIndex: number
  currentItem: CalibrationItem | null
  progress: number
  isLoading: boolean
  isComplete: boolean
  error: string | null
  like: () => void
  dislike: () => void
  retry: () => void
}

export function useCalibration(): UseCalibrationReturn {
  const [items, setItems] = useState<CalibrationItem[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const photoEmbeddings = useOnboardingStore((s) => s.photoEmbeddings)
  const setCalibrationItems = useOnboardingStore((s) => s.setCalibrationItems)
  const addLike = useOnboardingStore((s) => s.addLike)
  const addDislike = useOnboardingStore((s) => s.addDislike)

  // Track whether fetch has been initiated to avoid double-fetch in StrictMode
  const fetchInitiated = useRef(false)

  const fetchItems = useCallback(async () => {
    if (photoEmbeddings.length === 0) {
      setError('No photo embeddings available. Please upload photos first.')
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await api.post<{ items: CalibrationItem[]; total: number }>(
        '/onboarding/calibration-items/',
        { embeddings: photoEmbeddings }
      )

      const fetchedItems = response.data.items
      setItems(fetchedItems)
      setCalibrationItems(fetchedItems.map((item) => item.product_id))
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load calibration items'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [photoEmbeddings, setCalibrationItems])

  useEffect(() => {
    if (!fetchInitiated.current && photoEmbeddings.length > 0) {
      fetchInitiated.current = true
      fetchItems()
    }
  }, [fetchItems, photoEmbeddings.length])

  // Prefetch next image for smooth transitions
  useEffect(() => {
    const nextIndex = currentIndex + 1
    if (nextIndex < items.length) {
      const img = new Image()
      img.src = items[nextIndex].image_url
    }
  }, [currentIndex, items])

  const like = useCallback(() => {
    if (currentIndex < items.length) {
      addLike(items[currentIndex].product_id)
      setCurrentIndex((prev) => prev + 1)
    }
  }, [currentIndex, items, addLike])

  const dislike = useCallback(() => {
    if (currentIndex < items.length) {
      addDislike(items[currentIndex].product_id)
      setCurrentIndex((prev) => prev + 1)
    }
  }, [currentIndex, items, addDislike])

  const retry = useCallback(() => {
    fetchInitiated.current = false
    setCurrentIndex(0)
    fetchItems()
  }, [fetchItems])

  const total = items.length
  const isComplete = total > 0 && currentIndex >= total
  const currentItem = currentIndex < total ? items[currentIndex] : null
  const progress = total > 0 ? currentIndex / total : 0

  return {
    items,
    currentIndex,
    currentItem,
    progress,
    isLoading,
    isComplete,
    error,
    like,
    dislike,
    retry,
  }
}
