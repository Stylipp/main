import { Box, Typography } from '@mui/material'
import { motion } from 'framer-motion'
import { fadeInUp } from '../../utils/animations'
import type { Feature } from '../../types/landing.types'

interface FeatureCardProps {
  feature: Feature
  index?: number
  isActive?: boolean
  onClick?: () => void
}

const gradients = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
]

export const FeatureCard = ({ feature, index = 0, isActive, onClick }: FeatureCardProps) => {
  const gradient = gradients[index % gradients.length]

  return (
    <motion.div variants={fadeInUp}>
      <Box
        onClick={onClick}
        sx={{
          position: 'relative',
          cursor: onClick ? 'pointer' : 'default',
          p: 4,
          borderRadius: 4,
          bgcolor: 'white',
          border: '1px solid',
          borderColor: isActive ? 'primary.main' : 'rgba(0,0,0,0.06)',
          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          overflow: 'hidden',
          height: '100%',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 3,
            background: gradient,
            opacity: 0,
            transition: 'opacity 0.3s ease',
          },
          '&:hover': {
            transform: 'translateY(-8px)',
            boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
            borderColor: 'transparent',
            '&::before': {
              opacity: 1,
            },
            '& .feature-icon': {
              transform: 'scale(1.1)',
              background: gradient,
              '& svg': {
                color: 'white',
              },
            },
          },
        }}
      >
        <Box
          className="feature-icon"
          sx={{
            width: 56,
            height: 56,
            borderRadius: 3,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: 'rgba(91,74,228,0.08)',
            mb: 3,
            transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
            '& svg': {
              fontSize: 28,
              color: 'primary.main',
              transition: 'color 0.3s ease',
            },
          }}
        >
          {feature.icon}
        </Box>
        <Typography
          variant="h6"
          sx={{
            fontWeight: 700,
            mb: 1.5,
            fontSize: '1.1rem',
            color: 'text.primary',
          }}
        >
          {feature.title}
        </Typography>
        <Typography
          variant="body2"
          sx={{
            color: 'text.secondary',
            lineHeight: 1.7,
            fontSize: '0.9rem',
          }}
        >
          {feature.description}
        </Typography>
      </Box>
    </motion.div>
  )
}
