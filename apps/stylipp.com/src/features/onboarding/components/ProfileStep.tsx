import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import api from '@/shared/hooks/useApi'
import { useOnboardingStore } from '@/features/onboarding/stores/onboardingStore'
import { useAuthStore } from '@/features/auth/stores/authStore'

export default function ProfileStep() {
  const navigate = useNavigate()

  const photoEmbeddings = useOnboardingStore((s) => s.photoEmbeddings)
  const calibrationLikes = useOnboardingStore((s) => s.calibrationLikes)
  const calibrationDislikes = useOnboardingStore((s) => s.calibrationDislikes)
  const completeOnboarding = useOnboardingStore((s) => s.complete)
  const fetchMe = useAuthStore((s) => s.fetchMe)

  const [displayName, setDisplayName] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleComplete = async () => {
    setIsSubmitting(true)
    setError(null)

    try {
      await api.post('/onboarding/complete', {
        photo_embeddings: photoEmbeddings,
        liked_product_ids: calibrationLikes,
        disliked_product_ids: calibrationDislikes,
        ...(displayName.trim() && { display_name: displayName.trim() }),
      })

      // Refresh user data so onboarding_completed=true is reflected
      await fetchMe()

      // Mark onboarding as complete in local store
      completeOnboarding()

      navigate('/onboarding/complete')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to complete setup'
      setError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        gap: 3,
      }}
    >
      {/* Header */}
      <Box sx={{ textAlign: 'center', pt: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600, color: 'text.primary', mb: 1 }}>
          Almost There!
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Add your name (optional)
        </Typography>
      </Box>

      {/* Form */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          px: 2,
        }}
      >
        <TextField
          fullWidth
          label="Display Name"
          placeholder="How should we call you?"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          disabled={isSubmitting}
          inputProps={{ maxLength: 100 }}
          helperText="You can always change this later"
          sx={{ mb: 2 }}
        />

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
      </Box>

      {/* Complete button */}
      <Box sx={{ pb: 2 }}>
        <Button
          fullWidth
          variant="contained"
          size="large"
          onClick={handleComplete}
          disabled={isSubmitting}
          sx={{ py: 1.5 }}
        >
          {isSubmitting ? <CircularProgress size={24} color="inherit" /> : 'Complete Setup'}
        </Button>
      </Box>
    </Box>
  )
}
