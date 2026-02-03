import { Box, CardContent, Typography, Avatar } from '@mui/material'
import { FormatQuote } from '@mui/icons-material'
import { GlassCard } from '@/shared/components'
import type { Testimonial } from '../../types/landing.types'

interface TestimonialCardProps {
  testimonial: Testimonial
}

export const TestimonialCard = ({ testimonial }: TestimonialCardProps) => {
  return (
    <GlassCard
      sx={{
        height: '100%',
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
        },
      }}
    >
      <CardContent sx={{ p: 4, display: 'flex', flexDirection: 'column', height: '100%' }}>
        <FormatQuote
          sx={{
            fontSize: 40,
            color: 'primary.main',
            opacity: 0.5,
            transform: 'rotate(180deg)',
            mb: 2,
          }}
        />

        <Typography
          variant="h6"
          sx={{
            fontWeight: 500,
            mb: 2,
            color: 'text.primary',
            fontStyle: 'italic',
          }}
        >
          "{testimonial.quote}"
        </Typography>

        <Typography
          variant="body2"
          sx={{
            color: 'text.secondary',
            lineHeight: 1.7,
            mb: 3,
            flex: 1,
          }}
        >
          {testimonial.fullText}
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 'auto' }}>
          <Avatar
            src={testimonial.companyLogo}
            alt={testimonial.authorName}
            sx={{
              width: 48,
              height: 48,
              bgcolor: 'primary.main',
            }}
          >
            {testimonial.authorName.charAt(0)}
          </Avatar>
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              {testimonial.authorName}
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              {testimonial.authorRole}
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </GlassCard>
  )
}
