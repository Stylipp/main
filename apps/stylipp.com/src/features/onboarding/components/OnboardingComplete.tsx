import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import { useOnboardingStore } from '@/features/onboarding/stores/onboardingStore'

export default function OnboardingComplete() {
  const navigate = useNavigate()
  const reset = useOnboardingStore((s) => s.reset)

  // Clear onboarding store on mount — data is no longer needed
  const hasReset = useRef(false)
  useEffect(() => {
    if (!hasReset.current) {
      hasReset.current = true
      reset()
    }
  }, [reset])

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 3,
        px: 3,
      }}
    >
      <CheckCircleIcon
        sx={{
          fontSize: 80,
          color: 'primary.main',
        }}
      />

      <Typography variant="h4" sx={{ fontWeight: 700, textAlign: 'center' }}>
        You&apos;re All Set!
      </Typography>

      <Typography
        variant="body1"
        color="text.secondary"
        sx={{ textAlign: 'center', maxWidth: 300 }}
      >
        We&apos;ve learned your style. Your personalized feed is ready.
      </Typography>

      <Button
        variant="contained"
        size="large"
        onClick={() => navigate('/feed')}
        sx={{ mt: 2, px: 4, py: 1.5 }}
      >
        Start Discovering
      </Button>
    </Box>
  )
}
