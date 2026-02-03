import { Box, Typography, keyframes } from '@mui/material'

const scroll = keyframes`
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
`

const brands = ['ZARA', 'H&M', 'UNIQLO', 'MANGO', 'ASOS', 'NORDSTROM']

export const LogoCarousel = () => {
  const allBrands = [...brands, ...brands]

  return (
    <Box
      sx={{
        width: 400,
        overflow: 'hidden',
        position: 'relative',
        '&::before, &::after': {
          content: '""',
          position: 'absolute',
          top: 0,
          bottom: 0,
          width: 30,
          zIndex: 2,
          pointerEvents: 'none',
        },
        '&::before': {
          left: 0,
          background: 'linear-gradient(90deg, rgba(240,244,255,1) 0%, transparent 100%)',
        },
        '&::after': {
          right: 0,
          background: 'linear-gradient(270deg, rgba(240,244,255,1) 0%, transparent 100%)',
        },
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          animation: `${scroll} 15s linear infinite`,
        }}
      >
        {allBrands.map((brand, index) => (
          <Typography
            key={`${brand}-${index}`}
            sx={{
              fontWeight: 600,
              fontSize: '0.85rem',
              color: 'text.primary',
              opacity: 0.4,
              letterSpacing: 1,
              whiteSpace: 'nowrap',
              px: 2,
            }}
          >
            {brand}
          </Typography>
        ))}
      </Box>
    </Box>
  )
}
