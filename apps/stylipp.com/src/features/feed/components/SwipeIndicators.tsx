import Box from '@mui/material/Box'
import FavoriteIcon from '@mui/icons-material/Favorite'
import CloseIcon from '@mui/icons-material/Close'
import { motion, useTransform } from 'framer-motion'
import type { MotionValue } from 'framer-motion'

interface SwipeIndicatorsProps {
  x: MotionValue<number>
}

export function SwipeIndicators({ x }: SwipeIndicatorsProps) {
  const likeOpacity = useTransform(x, [0, 100], [0, 1])
  const dislikeOpacity = useTransform(x, [-100, 0], [1, 0])

  return (
    <>
      {/* LIKE indicator — top-right */}
      <motion.div
        style={{
          opacity: likeOpacity,
          position: 'absolute',
          top: 24,
          right: 24,
          zIndex: 10,
          pointerEvents: 'none',
          transform: 'rotate(-15deg)',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
            border: '3px solid',
            borderColor: 'success.main',
            borderRadius: '8px',
            px: 1.5,
            py: 0.5,
          }}
        >
          <FavoriteIcon sx={{ color: 'success.main', fontSize: 20 }} />
          <Box
            component="span"
            sx={{
              color: 'success.main',
              fontWeight: 800,
              fontSize: '1.25rem',
              textTransform: 'uppercase',
              letterSpacing: 2,
            }}
          >
            LIKE
          </Box>
        </Box>
      </motion.div>

      {/* DISLIKE indicator — top-left */}
      <motion.div
        style={{
          opacity: dislikeOpacity,
          position: 'absolute',
          top: 24,
          left: 24,
          zIndex: 10,
          pointerEvents: 'none',
          transform: 'rotate(15deg)',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
            border: '3px solid',
            borderColor: 'error.main',
            borderRadius: '8px',
            px: 1.5,
            py: 0.5,
          }}
        >
          <CloseIcon sx={{ color: 'error.main', fontSize: 20 }} />
          <Box
            component="span"
            sx={{
              color: 'error.main',
              fontWeight: 800,
              fontSize: '1.25rem',
              textTransform: 'uppercase',
              letterSpacing: 2,
            }}
          >
            NOPE
          </Box>
        </Box>
      </motion.div>
    </>
  )
}
