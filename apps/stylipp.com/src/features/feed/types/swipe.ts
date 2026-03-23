export type SwipeDirection = 'left' | 'right'
export type SwipeAction = 'like' | 'dislike' | 'save'

export interface FeedItem {
  product_id: string
  title: string
  price: number
  currency: string
  image_url: string
  product_url: string
  score: number
  explanation: string
}

export interface FeedResponse {
  items: FeedItem[]
  next_cursor: string | null
  has_more: boolean
  total_in_batch: number
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
