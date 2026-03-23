import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import ExploreIcon from '@mui/icons-material/Explore'

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
        px: 3,
        width: '90vw',
        maxWidth: 400,
      }}
    >
      <ExploreIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2, opacity: 0.5 }} />
      <Typography variant="h5" sx={{ fontWeight: 600, color: 'text.primary', mb: 1 }}>
        You've seen everything!
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Check back later for new recommendations
      </Typography>
      <Button variant="outlined" onClick={onRefresh}>
        Refresh Feed
      </Button>
    </Box>
  )
}
