import { Card, type CardProps, styled } from '@mui/material'

export const GlassCard = styled(Card)<CardProps>(() => ({
  background: '#ffffff',
  boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
  border: '1px solid rgba(0,0,0,0.06)',
  borderRadius: 16,
}))
