import { Box, Chip, Grid, Typography } from '@mui/material'
import { motion } from 'framer-motion'
import { Psychology, AccessTime, Translate, PersonOutline } from '@mui/icons-material'
import { SectionContainer, GlassCard } from '@/shared/components'
import { fadeInUp, staggerContainer } from '../../utils/animations'
import type { Benefit } from '../../types/landing.types'

const benefits: Benefit[] = [
  {
    id: '1',
    icon: <Psychology />,
    title: 'Continuously Learning',
    description:
      'Our AI evolves with your style preferences, getting smarter with every interaction.',
  },
  {
    id: '2',
    icon: <AccessTime />,
    title: '24/7 Available',
    description: 'Get styling advice anytime, anywhere. Your personal stylist never sleeps.',
  },
  {
    id: '3',
    icon: <Translate />,
    title: 'Multilingual',
    description: 'Supports Hebrew and English, making fashion accessible to everyone.',
  },
  {
    id: '4',
    icon: <PersonOutline />,
    title: 'Personalized',
    description:
      'Tailored to your body type, preferences, and lifestyle for perfect recommendations.',
  },
]

export const BenefitsSection = () => {
  return (
    <SectionContainer component="section" maxWidth="lg">
      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-100px' }}
        variants={staggerContainer}
      >
        <Box sx={{ textAlign: 'center', mb: 6 }}>
          <motion.div variants={fadeInUp}>
            <Chip
              label="Benefits"
              sx={{
                mb: 2,
                bgcolor: 'rgba(91,74,228,0.1)',
                color: 'primary.main',
                fontWeight: 500,
              }}
            />
          </motion.div>
          <motion.div variants={fadeInUp}>
            <Typography variant="h2" sx={{ mb: 2 }}>
              Why choose Stylipp?
            </Typography>
          </motion.div>
          <motion.div variants={fadeInUp}>
            <Typography variant="body1" sx={{ color: 'text.secondary', maxWidth: 500, mx: 'auto' }}>
              Experience the future of personal styling with our advanced AI technology.
            </Typography>
          </motion.div>
        </Box>

        <Grid container spacing={3}>
          {benefits.map((benefit) => (
            <Grid size={{ xs: 12, sm: 6 }} key={benefit.id}>
              <motion.div variants={fadeInUp}>
                <GlassCard
                  sx={{
                    p: 3,
                    height: '100%',
                    display: 'flex',
                    gap: 2,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
                    },
                  }}
                >
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 2,
                      background:
                        'linear-gradient(135deg, rgba(91,74,228,0.1), rgba(123,107,240,0.1))',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      '& svg': {
                        fontSize: 24,
                        color: 'primary.main',
                      },
                    }}
                  >
                    {benefit.icon}
                  </Box>
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                      {benefit.title}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary', lineHeight: 1.6 }}>
                      {benefit.description}
                    </Typography>
                  </Box>
                </GlassCard>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      </motion.div>
    </SectionContainer>
  )
}
