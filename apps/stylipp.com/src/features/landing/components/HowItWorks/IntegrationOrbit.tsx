import { Box, keyframes } from '@mui/material'
import { Instagram, Pinterest, ShoppingBag, AutoAwesome } from '@mui/icons-material'

const orbit = keyframes`
  from { transform: rotate(0deg) translateX(120px) rotate(0deg); }
  to { transform: rotate(360deg) translateX(120px) rotate(-360deg); }
`

const orbitReverse = keyframes`
  from { transform: rotate(360deg) translateX(90px) rotate(-360deg); }
  to { transform: rotate(0deg) translateX(90px) rotate(0deg); }
`

const pulse = keyframes`
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.8; }
`

const orbitingIcons = [
  { Icon: Instagram, delay: 0 },
  { Icon: Pinterest, delay: 2.5 },
  { Icon: ShoppingBag, delay: 5 },
  { Icon: AutoAwesome, delay: 7.5 },
]

export const IntegrationOrbit = () => {
  return (
    <Box
      sx={{
        position: 'relative',
        width: { xs: 280, md: 320 },
        height: { xs: 280, md: 320 },
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        mx: 'auto',
      }}
    >
      {/* Outer orbit ring */}
      <Box
        sx={{
          position: 'absolute',
          width: 240,
          height: 240,
          borderRadius: '50%',
          border: '1px dashed rgba(91,74,228,0.3)',
        }}
      />

      {/* Inner orbit ring */}
      <Box
        sx={{
          position: 'absolute',
          width: 180,
          height: 180,
          borderRadius: '50%',
          border: '1px dashed rgba(91,74,228,0.2)',
        }}
      />

      {/* Central circle with gradient */}
      <Box
        sx={{
          width: 80,
          height: 80,
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #5B4AE4 0%, #7B6BF0 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          animation: `${pulse} 3s ease-in-out infinite`,
          boxShadow: '0 0 40px rgba(91,74,228,0.3)',
          zIndex: 2,
        }}
      >
        <AutoAwesome sx={{ fontSize: 36, color: 'white' }} />
      </Box>

      {/* Orbiting icons */}
      {orbitingIcons.map(({ Icon, delay }, index) => (
        <Box
          key={index}
          sx={{
            position: 'absolute',
            animation:
              index % 2 === 0
                ? `${orbit} 10s linear infinite`
                : `${orbitReverse} 12s linear infinite`,
            animationDelay: `${delay}s`,
          }}
        >
          <Box
            sx={{
              width: 40,
              height: 40,
              borderRadius: '50%',
              bgcolor: 'white',
              border: '1px solid rgba(0,0,0,0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            }}
          >
            <Icon sx={{ fontSize: 20, color: 'primary.main' }} />
          </Box>
        </Box>
      ))}
    </Box>
  )
}
