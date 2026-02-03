import { Box, Button, IconButton, Typography } from '@mui/material'
import { Close as CloseIcon, ArrowForward as ArrowIcon } from '@mui/icons-material'

interface AnnouncementBannerProps {
  onDismiss?: () => void
}

export const AnnouncementBanner = ({ onDismiss }: AnnouncementBannerProps) => {
  return (
    <Box
      sx={{
        background: 'linear-gradient(90deg, #5B4AE4 0%, #7B6BF0 100%)',
        py: 1.5,
        px: 2,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 2,
      }}
    >
      <Typography variant="body2" sx={{ color: 'white', fontWeight: 500 }}>
        🎉 Stylipp Named Best AI Styling App 2026
      </Typography>
      <Button
        endIcon={<ArrowIcon sx={{ fontSize: 16 }} />}
        sx={{
          color: '#5B4AE4',
          bgcolor: 'white',
          borderRadius: 5,
          px: 2,
          py: 0.5,
          fontSize: '0.8rem',
          fontWeight: 600,
          textTransform: 'none',
          '&:hover': {
            bgcolor: 'rgba(255,255,255,0.9)',
          },
        }}
      >
        Learn More
      </Button>
      <IconButton
        size="small"
        onClick={onDismiss}
        sx={{ color: 'white', ml: 'auto', opacity: 0.8 }}
        aria-label="Dismiss announcement"
      >
        <CloseIcon fontSize="small" />
      </IconButton>
    </Box>
  )
}
