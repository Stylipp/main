import api from '@/shared/hooks/useApi'
import type { FeedResponse, SwipeAction } from '../types/swipe'

export async function fetchFeed(cursor?: string, pageSize: number = 20): Promise<FeedResponse> {
  const params: Record<string, string | number> = { page_size: pageSize }
  if (cursor) params.cursor = cursor
  const { data } = await api.get<FeedResponse>('/feed/', { params })
  return data
}

export async function submitFeedback(productId: string, action: SwipeAction): Promise<void> {
  await api.post('/feedback/', { product_id: productId, action })
}
