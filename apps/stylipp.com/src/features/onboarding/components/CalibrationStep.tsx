import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Card from '@mui/material/Card'
import CardMedia from '@mui/material/CardMedia'
import IconButton from '@mui/material/IconButton'
import Button from '@mui/material/Button'
import LinearProgress from '@mui/material/LinearProgress'
import Skeleton from '@mui/material/Skeleton'
import ThumbUpIcon from '@mui/icons-material/ThumbUp'
import ThumbDownIcon from '@mui/icons-material/ThumbDown'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'
import { motion, AnimatePresence } from 'framer-motion'
import { useCalibration } from '@/features/onboarding/hooks/useCalibration'

const cardVariants = {
  enter: {
    opacity: 0,
    scale: 0.95,
  },
  center: {
    opacity: 1,
    scale: 1,
  },
  exit: {
    opacity: 0,
    scale: 0.95,
  },
}

export default function CalibrationStep() {
  const navigate = useNavigate()
  const {
    currentIndex,
    currentItem,
    progress,
    isLoading,
    isComplete,
    error,
    like,
    dislike,
    retry,
    items,
  } = useCalibration()

  // Auto-navigate to profile step when calibration is complete
  useEffect(() => {
    if (isComplete) {
      navigate('/onboarding/profile')
    }
  }, [isComplete, navigate])

  const total = items.length

  // Loading state
  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          gap: 2,
        }}
      >
        <Box sx={{ textAlign: 'center', pt: 2 }}>
          <Typography variant="h5" sx={{ fontWeight: 600, color: 'text.primary', mb: 1 }}>
            Discover Your Style
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Loading your personalized items...
          </Typography>
        </Box>

        <Box sx={{ px: 2 }}>
          <Skeleton variant="rounded" sx={{ width: '100%', height: 8, borderRadius: 4 }} />
        </Box>

        <Box
          sx={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            px: 2,
          }}
        >
          <Box sx={{ width: '80%', maxWidth: 320 }}>
            <Skeleton
              variant="rounded"
              sx={{
                width: '100%',
                aspectRatio: '3/4',
                borderRadius: 2,
              }}
            />
            <Skeleton variant="text" sx={{ mt: 1.5, width: '70%' }} />
            <Skeleton variant="text" sx={{ width: '30%' }} />
          </Box>
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 6, pb: 3 }}>
          <Skeleton variant="circular" width={56} height={56} />
          <Skeleton variant="circular" width={56} height={56} />
        </Box>
      </Box>
    )
  }

  // Error state
  if (error) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 2,
          px: 3,
        }}
      >
        <ErrorOutlineIcon sx={{ fontSize: 56, color: 'error.main', opacity: 0.8 }} />
        <Typography variant="h6" sx={{ fontWeight: 600, textAlign: 'center' }}>
          Something went wrong
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
          {error}
        </Typography>
        <Button variant="contained" onClick={retry} sx={{ mt: 1 }}>
          Try Again
        </Button>
      </Box>
    )
  }

  // Empty items state
  if (total === 0) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 2,
          px: 3,
        }}
      >
        <ErrorOutlineIcon sx={{ fontSize: 56, color: 'warning.main', opacity: 0.8 }} />
        <Typography variant="h6" sx={{ fontWeight: 600, textAlign: 'center' }}>
          No items available
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
          We couldn&apos;t find calibration items. Please try again.
        </Typography>
        <Button variant="contained" onClick={retry} sx={{ mt: 1 }}>
          Retry
        </Button>
      </Box>
    )
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        gap: 2,
      }}
    >
      {/* Header */}
      <Box sx={{ textAlign: 'center', pt: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600, color: 'text.primary', mb: 1 }}>
          Discover Your Style
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Like or pass on these items ({currentIndex + 1} of {total})
        </Typography>
      </Box>

      {/* Progress bar */}
      <Box sx={{ px: 2 }}>
        <LinearProgress
          variant="determinate"
          value={progress * 100}
          sx={{
            height: 8,
            borderRadius: 4,
            bgcolor: 'action.hover',
            '& .MuiLinearProgress-bar': {
              borderRadius: 4,
            },
          }}
        />
      </Box>

      {/* Product card area */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          px: 2,
          overflow: 'hidden',
        }}
      >
        <AnimatePresence mode="wait">
          {currentItem && (
            <motion.div
              key={currentItem.product_id}
              variants={cardVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ type: 'tween', ease: 'easeOut', duration: 0.25 }}
              style={{ width: '80%', maxWidth: 320 }}
            >
              <Card
                elevation={2}
                sx={{
                  borderRadius: 2,
                  overflow: 'hidden',
                }}
              >
                <CardMedia
                  component="img"
                  image={currentItem.image_url}
                  alt={currentItem.title}
                  sx={{
                    aspectRatio: '3/4',
                    objectFit: 'cover',
                  }}
                />
              </Card>

              {/* Title and price below card */}
              <Typography
                variant="subtitle1"
                sx={{
                  fontWeight: 500,
                  mt: 1.5,
                  textAlign: 'center',
                  lineHeight: 1.3,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {currentItem.title}
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ textAlign: 'center', mt: 0.25 }}
              >
                {currentItem.currency} {currentItem.price.toFixed(2)}
              </Typography>
            </motion.div>
          )}
        </AnimatePresence>
      </Box>

      {/* Action buttons */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: 6,
          pb: 3,
        }}
      >
        <IconButton
          onClick={dislike}
          disabled={!currentItem}
          aria-label="Dislike"
          sx={{
            width: 56,
            height: 56,
            bgcolor: 'error.light',
            color: 'error.contrastText',
            '&:hover': {
              bgcolor: 'error.main',
            },
            '&.Mui-disabled': {
              bgcolor: 'action.disabledBackground',
            },
          }}
        >
          <ThumbDownIcon sx={{ fontSize: 28 }} />
        </IconButton>

        <IconButton
          onClick={like}
          disabled={!currentItem}
          aria-label="Like"
          sx={{
            width: 56,
            height: 56,
            bgcolor: 'success.light',
            color: 'success.contrastText',
            '&:hover': {
              bgcolor: 'success.main',
            },
            '&.Mui-disabled': {
              bgcolor: 'action.disabledBackground',
            },
          }}
        >
          <ThumbUpIcon sx={{ fontSize: 28 }} />
        </IconButton>
      </Box>
    </Box>
  )
}
