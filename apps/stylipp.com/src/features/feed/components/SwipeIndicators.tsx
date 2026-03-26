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
          top: 20,
          right: 20,
          zIndex: 10,
          pointerEvents: 'none',
          transform: 'rotate(-12deg)',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 0.75,
            bgcolor: 'rgba(34, 197, 94, 0.15)',
            backdropFilter: 'blur(8px)',
            border: '3px solid',
            borderColor: 'success.main',
            borderRadius: '10px',
            px: 2,
            py: 0.75,
          }}
        >
          <FavoriteIcon sx={{ color: 'success.main', fontSize: 22 }} />
          <Box
            component="span"
            sx={{
              color: 'success.main',
              fontFamily: '"Syne", sans-serif',
              fontWeight: 800,
              fontSize: '1.2rem',
              textTransform: 'uppercase',
              letterSpacing: 3,
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
          top: 20,
          left: 20,
          zIndex: 10,
          pointerEvents: 'none',
          transform: 'rotate(12deg)',
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 0.75,
            bgcolor: 'rgba(239, 68, 68, 0.15)',
            backdropFilter: 'blur(8px)',
            border: '3px solid',
            borderColor: 'error.main',
            borderRadius: '10px',
            px: 2,
            py: 0.75,
          }}
        >
          <CloseIcon sx={{ color: 'error.main', fontSize: 22 }} />
          <Box
            component="span"
            sx={{
              color: 'error.main',
              fontFamily: '"Syne", sans-serif',
              fontWeight: 800,
              fontSize: '1.2rem',
              textTransform: 'uppercase',
              letterSpacing: 3,
            }}
          >
            NOPE
          </Box>
        </Box>
      </motion.div>
    </>
  )
}
