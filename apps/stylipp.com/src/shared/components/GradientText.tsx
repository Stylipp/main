import { Typography, type TypographyProps, styled } from '@mui/material'

export const GradientText = styled(Typography)<TypographyProps>(() => ({
  background: 'linear-gradient(135deg, #5B4AE4 0%, #7B6BF0 50%, #EC4899 100%)',
  backgroundClip: 'text',
  WebkitBackgroundClip: 'text',
  color: 'transparent',
}))
