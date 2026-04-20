export type SwipeDirection = 'left' | 'right'
export type SwipeAction = 'like' | 'dislike' | 'save'
export type ProductCategory =
  | 'shoes'
  | 'tops'
  | 'pants'
  | 'dresses'
  | 'jackets'
  | 'bags'
  | 'accessories'
  | 'other'
export type FeedCategory = 'all' | ProductCategory
export type FeedMode = 'trending' | 'hybrid' | 'personalized'

export const FEED_CATEGORY_OPTIONS: { value: FeedCategory; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'shoes', label: 'Shoes' },
  { value: 'tops', label: 'Tops' },
  { value: 'pants', label: 'Bottoms' },
  { value: 'dresses', label: 'Dresses' },
  { value: 'jackets', label: 'Outerwear' },
  { value: 'bags', label: 'Bags' },
  { value: 'accessories', label: 'Accessories' },
  { value: 'other', label: 'Other' },
]

export function formatCategoryLabel(category: ProductCategory): string {
  const match = FEED_CATEGORY_OPTIONS.find((option) => option.value === category)
  return match?.label ?? category
}

export interface FeedItem {
  product_id: string
  title: string
  price: number
  currency: string
  image_url: string
  product_url: string
  category: ProductCategory
  score: number
  explanation: string
}

export interface FeedResponse {
  items: FeedItem[]
  next_cursor: string | null
  has_more: boolean
  total_in_batch: number
  active_category: ProductCategory | null
  feed_mode: FeedMode
}

export interface SwipeRecord {
  productId: string
  action: SwipeAction
  timestamp: number
}

export interface PendingFeedback {
  productId: string
  action: SwipeAction
  retryCount: number
}

export interface ExposureEvent {
  product_id: string
  session_id: string
  feed_mode: FeedMode
  position: number
  shown_at: string
  action?: SwipeAction
  action_at?: string
  dwell_ms?: number
}
