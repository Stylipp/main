import { Button, type ButtonProps, styled } from '@mui/material'

export const GradientButton = styled(Button)<ButtonProps>(() => ({
  background: 'linear-gradient(135deg, #5B4AE4 0%, #7B6BF0 100%)',
  color: '#fff',
  padding: '12px 32px',
  borderRadius: 8,
  '&:hover': {
    background: 'linear-gradient(135deg, #4338CA 0%, #5B4AE4 100%)',
  },
}))
