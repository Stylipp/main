import Box from '@mui/material/Box'
import Card from '@mui/material/Card'
import CardMedia from '@mui/material/CardMedia'
import Typography from '@mui/material/Typography'
import OpenInNewIcon from '@mui/icons-material/OpenInNew'
import { AnimatePresence, motion, useMotionValue, useTransform } from 'framer-motion'
import type { PanInfo } from 'framer-motion'
import { formatCategoryLabel, type FeedItem, type SwipeDirection } from '../types/swipe'
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
  const rotate = useTransform(x, [-200, 200], [-12, 12])

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
          width: 'calc(100vw - 32px)',
          maxWidth: 380,
          pointerEvents: isTop ? 'auto' : 'none',
        }}
        drag={isTop ? 'x' : false}
        dragSnapToOrigin
        dragElastic={0.7}
        dragTransition={{ bounceStiffness: 300, bounceDamping: 20 }}
        whileDrag={{ cursor: 'grabbing', scale: 1.02 }}
        onDragEnd={handleDragEnd}
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1, transition: { duration: 0.25, ease: 'easeOut' } }}
        exit={{
          x: exitX,
          opacity: 0,
          rotate: exitX > 0 ? 18 : -18,
          transition: { duration: 0.3, ease: 'easeIn' },
        }}
      >
        <Card
          sx={{
            borderRadius: '20px',
            overflow: 'hidden',
            boxShadow: '0 12px 40px rgba(0,0,0,0.15)',
            position: 'relative',
            cursor: isTop ? 'grab' : 'default',
            border: 'none',
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

          {/* Card content overlay */}
          <Box
            sx={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              background:
                'linear-gradient(0deg, rgba(0,0,0,0.65) 0%, rgba(0,0,0,0.3) 50%, transparent 100%)',
              p: 2.5,
              pt: 8,
            }}
          >
            <Box
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                borderRadius: '999px',
                bgcolor: 'rgba(255,255,255,0.16)',
                px: 1,
                py: 0.4,
                mb: 1,
                backdropFilter: 'blur(10px)',
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  color: '#ffffff',
                  fontWeight: 700,
                  fontSize: '0.68rem',
                  letterSpacing: '0.04em',
                  textTransform: 'uppercase',
                }}
              >
                {formatCategoryLabel(item.category)}
              </Typography>
            </Box>

            <Typography
              variant="subtitle1"
              sx={{
                fontFamily: '"Syne", "Manrope", sans-serif',
                fontWeight: 700,
                color: '#ffffff',
                lineHeight: 1.3,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                fontSize: '1.05rem',
              }}
            >
              {item.title}
            </Typography>

            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                mt: 0.5,
              }}
            >
              <Typography
                variant="body2"
                sx={{
                  color: '#ffffff',
                  fontWeight: 700,
                  fontSize: '1rem',
                  letterSpacing: '-0.01em',
                }}
              >
                {item.currency} {item.price.toFixed(2)}
              </Typography>

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
                  color: 'rgba(255,255,255,0.75)',
                  fontSize: '0.75rem',
                  fontWeight: 500,
                  textDecoration: 'none',
                  cursor: 'pointer',
                  transition: 'color 0.2s ease',
                  '&:hover': {
                    color: '#ffffff',
                  },
                }}
              >
                View
                <OpenInNewIcon sx={{ fontSize: 13 }} />
              </Box>
            </Box>

            {item.explanation && (
              <Typography
                variant="caption"
                sx={{
                  color: 'rgba(255,255,255,0.6)',
                  display: 'block',
                  mt: 0.75,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  fontSize: '0.7rem',
                  fontWeight: 500,
                  letterSpacing: '0.02em',
                }}
              >
                {item.explanation}
              </Typography>
            )}
          </Box>
        </Card>
      </motion.div>
    </AnimatePresence>
  )
}
