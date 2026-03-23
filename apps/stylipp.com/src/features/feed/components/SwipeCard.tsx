import Box from '@mui/material/Box'
import Card from '@mui/material/Card'
import CardMedia from '@mui/material/CardMedia'
import Typography from '@mui/material/Typography'
import OpenInNewIcon from '@mui/icons-material/OpenInNew'
import { AnimatePresence, motion, useMotionValue, useTransform } from 'framer-motion'
import type { PanInfo } from 'framer-motion'
import type { FeedItem, SwipeDirection } from '../types/swipe'
import { SwipeIndicators } from './SwipeIndicators'

const SWIPE_OFFSET_THRESHOLD = 100
const SWIPE_VELOCITY_THRESHOLD = 500

interface SwipeCardProps {
  item: FeedItem
  isTop: boolean
  onSwipe: (direction: SwipeDirection) => void
  exitX: number
}

export function SwipeCard({ item, isTop, onSwipe, exitX }: SwipeCardProps) {
  const x = useMotionValue(0)
  const rotate = useTransform(x, [-200, 200], [-15, 15])

  const handleDragEnd = (_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    const { offset, velocity } = info

    if (offset.x > SWIPE_OFFSET_THRESHOLD || velocity.x > SWIPE_VELOCITY_THRESHOLD) {
      onSwipe('right')
    } else if (offset.x < -SWIPE_OFFSET_THRESHOLD || velocity.x < -SWIPE_VELOCITY_THRESHOLD) {
      onSwipe('left')
    }
  }

  return (
    <AnimatePresence mode="popLayout">
      <motion.div
        key={item.product_id}
        style={{
          x,
          rotate,
          touchAction: 'none',
          width: '90vw',
          maxWidth: 400,
          position: 'absolute',
          pointerEvents: isTop ? 'auto' : 'none',
        }}
        drag={isTop ? 'x' : false}
        dragSnapToOrigin
        dragElastic={0.7}
        dragTransition={{ bounceStiffness: 300, bounceDamping: 20 }}
        whileDrag={{ cursor: 'grabbing', scale: 1.02 }}
        onDragEnd={handleDragEnd}
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1, transition: { duration: 0.3 } }}
        exit={{
          x: exitX,
          opacity: 0,
          rotate: exitX > 0 ? 20 : -20,
          transition: { duration: 0.3 },
        }}
      >
        <Card
          sx={{
            borderRadius: '16px',
            overflow: 'hidden',
            boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
            position: 'relative',
            cursor: isTop ? 'grab' : 'default',
          }}
        >
          {/* Swipe indicators overlay */}
          <SwipeIndicators x={x} />

          <CardMedia
            component="img"
            image={item.image_url}
            alt={item.title}
            sx={{
              aspectRatio: '3/4',
              objectFit: 'cover',
              userSelect: 'none',
              pointerEvents: 'none',
            }}
          />

          {/* Card content overlay at bottom */}
          <Box
            sx={{
              p: 2,
              background: 'linear-gradient(transparent, rgba(0,0,0,0.7))',
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
            }}
          >
            <Typography
              variant="subtitle1"
              sx={{
                fontWeight: 600,
                color: '#ffffff',
                lineHeight: 1.3,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {item.title}
            </Typography>

            <Typography
              variant="body2"
              sx={{
                color: 'rgba(255,255,255,0.9)',
                fontWeight: 600,
                mt: 0.25,
              }}
            >
              {item.currency} {item.price.toFixed(2)}
            </Typography>

            {item.explanation && (
              <Typography
                variant="caption"
                sx={{
                  color: 'rgba(255,255,255,0.7)',
                  display: 'block',
                  mt: 0.5,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {item.explanation}
              </Typography>
            )}

            <Box
              component="a"
              href={item.product_url}
              target="_blank"
              rel="noopener noreferrer"
              onPointerDownCapture={(e: React.PointerEvent) => e.stopPropagation()}
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 0.5,
                mt: 1,
                color: 'rgba(255,255,255,0.8)',
                fontSize: '0.75rem',
                textDecoration: 'none',
                '&:hover': {
                  color: '#ffffff',
                  textDecoration: 'underline',
                },
              }}
            >
              View product
              <OpenInNewIcon sx={{ fontSize: 14 }} />
            </Box>
          </Box>
        </Card>
      </motion.div>
    </AnimatePresence>
  )
}
