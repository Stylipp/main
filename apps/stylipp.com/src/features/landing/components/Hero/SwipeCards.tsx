import { useState, useEffect } from 'react'
import { Box, Typography, Avatar } from '@mui/material'
import { motion, AnimatePresence } from 'framer-motion'
import { Favorite, Close } from '@mui/icons-material'

interface ClothingItem {
  id: number
  image: string
  name: string
  brand: string
  price: string
}

const clothingItems: ClothingItem[] = [
  { id: 1, image: '👗', name: 'Summer Dress', brand: 'Zara', price: '$89' },
  { id: 2, image: '👔', name: 'Classic Blazer', brand: 'H&M', price: '$129' },
  { id: 3, image: '👖', name: 'Slim Fit Jeans', brand: "Levi's", price: '$98' },
  { id: 4, image: '👟', name: 'White Sneakers', brand: 'Nike', price: '$110' },
  { id: 5, image: '👜', name: 'Leather Bag', brand: 'Coach', price: '$250' },
]

export const SwipeCards = () => {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [direction, setDirection] = useState<'left' | 'right' | null>(null)

  useEffect(() => {
    const interval = setInterval(() => {
      setDirection(Math.random() > 0.5 ? 'right' : 'left')
      setTimeout(() => {
        setCurrentIndex((prev) => (prev + 1) % clothingItems.length)
        setDirection(null)
      }, 400)
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  const currentItem = clothingItems[currentIndex]
  const nextItem = clothingItems[(currentIndex + 1) % clothingItems.length]

  return (
    <Box
      sx={{
        position: 'relative',
        width: { xs: 280, md: 320 },
        height: { xs: 380, md: 420 },
      }}
    >
      {/* Chat bubble */}
      <Box
        component={motion.div}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        sx={{
          position: 'absolute',
          top: -20,
          right: -40,
          bgcolor: 'white',
          borderRadius: 3,
          px: 2,
          py: 1.5,
          boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          zIndex: 10,
        }}
      >
        <Typography variant="body2" sx={{ color: 'text.secondary', fontSize: '0.85rem' }}>
          What's your style today?
        </Typography>
        <Avatar
          sx={{
            width: 32,
            height: 32,
            bgcolor: 'primary.light',
            fontSize: '0.9rem',
          }}
        >
          👩
        </Avatar>
      </Box>

      {/* Background card (next item) */}
      <Box
        sx={{
          position: 'absolute',
          top: 20,
          left: 20,
          width: '100%',
          height: '100%',
          bgcolor: 'white',
          borderRadius: 4,
          boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          border: '1px solid rgba(0,0,0,0.06)',
        }}
      >
        <Typography sx={{ fontSize: '4rem' }}>{nextItem.image}</Typography>
      </Box>

      {/* Main swipe card */}
      <AnimatePresence mode="wait">
        <Box
          component={motion.div}
          key={currentItem.id}
          initial={{ scale: 1, x: 0, rotate: 0 }}
          animate={{
            scale: direction ? 0.95 : 1,
            x: direction === 'right' ? 200 : direction === 'left' ? -200 : 0,
            rotate: direction === 'right' ? 15 : direction === 'left' ? -15 : 0,
            opacity: direction ? 0 : 1,
          }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            bgcolor: 'white',
            borderRadius: 4,
            boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            border: '1px solid rgba(0,0,0,0.06)',
            cursor: 'grab',
          }}
        >
          {/* Like/Dislike indicator */}
          <AnimatePresence>
            {direction && (
              <Box
                component={motion.div}
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                sx={{
                  position: 'absolute',
                  top: 20,
                  left: direction === 'right' ? 20 : 'auto',
                  right: direction === 'left' ? 20 : 'auto',
                  zIndex: 10,
                  bgcolor: direction === 'right' ? '#22c55e' : '#ef4444',
                  borderRadius: 2,
                  px: 2,
                  py: 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.5,
                }}
              >
                {direction === 'right' ? (
                  <Favorite sx={{ color: 'white', fontSize: 20 }} />
                ) : (
                  <Close sx={{ color: 'white', fontSize: 20 }} />
                )}
                <Typography sx={{ color: 'white', fontWeight: 600, fontSize: '0.85rem' }}>
                  {direction === 'right' ? 'LIKE' : 'NOPE'}
                </Typography>
              </Box>
            )}
          </AnimatePresence>

          {/* Image area */}
          <Box
            sx={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              bgcolor: '#f8f9fc',
            }}
          >
            <Typography sx={{ fontSize: '6rem' }}>{currentItem.image}</Typography>
          </Box>

          {/* Info area */}
          <Box sx={{ p: 2.5, borderTop: '1px solid rgba(0,0,0,0.06)' }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, color: 'text.primary' }}>
              {currentItem.name}
            </Typography>
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                mt: 0.5,
              }}
            >
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                {currentItem.brand}
              </Typography>
              <Typography variant="subtitle2" sx={{ color: 'primary.main', fontWeight: 600 }}>
                {currentItem.price}
              </Typography>
            </Box>
          </Box>
        </Box>
      </AnimatePresence>

      {/* Action buttons */}
      <Box
        sx={{
          position: 'absolute',
          bottom: -60,
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          gap: 2,
        }}
      >
        <Box
          component={motion.div}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          sx={{
            width: 48,
            height: 48,
            borderRadius: '50%',
            bgcolor: 'white',
            boxShadow: '0 4px 12px rgba(239,68,68,0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            border: '2px solid #ef4444',
          }}
        >
          <Close sx={{ color: '#ef4444', fontSize: 24 }} />
        </Box>
        <Box
          component={motion.div}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          sx={{
            width: 48,
            height: 48,
            borderRadius: '50%',
            bgcolor: '#22c55e',
            boxShadow: '0 4px 12px rgba(34,197,94,0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
          }}
        >
          <Favorite sx={{ color: 'white', fontSize: 24 }} />
        </Box>
      </Box>
    </Box>
  )
}
