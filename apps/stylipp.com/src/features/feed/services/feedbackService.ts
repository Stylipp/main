import api from '@/shared/hooks/useApi'
import type { FeedCategory, FeedResponse, SwipeAction } from '../types/swipe'

export async function fetchFeed(
  cursor?: string,
  pageSize: number = 20,
  category: FeedCategory = 'all'
): Promise<FeedResponse> {
  const params: Record<string, string | number> = { page_size: pageSize }
  if (cursor) params.cursor = cursor
  if (category !== 'all') params.category = category
  const { data } = await api.get<FeedResponse>('/feed/', { params })
  return data
}

export async function submitFeedback(productId: string, action: SwipeAction): Promise<void> {
  await api.post('/feedback/', { product_id: productId, action })
}
