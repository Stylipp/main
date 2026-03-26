import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'

interface FeedEmptyStateProps {
  onRefresh: () => void
}

export function FeedEmptyState({ onRefresh }: FeedEmptyStateProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        px: 4,
        width: '100%',
        maxWidth: 380,
      }}
    >
      <Box
        sx={{
          width: 72,
          height: 72,
          borderRadius: '50%',
          bgcolor: 'rgba(91, 74, 228, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mb: 3,
        }}
      >
        <AutoAwesomeIcon sx={{ fontSize: 32, color: 'primary.main' }} />
      </Box>
      <Typography
        variant="h6"
        sx={{
          fontFamily: '"Syne", sans-serif',
          fontWeight: 700,
          color: 'text.primary',
          mb: 1,
        }}
      >
        You've seen everything!
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3, lineHeight: 1.6 }}>
        Check back later for new recommendations
      </Typography>
      <Button
        variant="contained"
        onClick={onRefresh}
        disableElevation
        sx={{
          borderRadius: 12,
          px: 4,
          py: 1.25,
          bgcolor: 'primary.main',
          fontWeight: 600,
          '&:hover': {
            bgcolor: 'primary.dark',
          },
        }}
      >
        Refresh Feed
      </Button>
    </Box>
  )
}
