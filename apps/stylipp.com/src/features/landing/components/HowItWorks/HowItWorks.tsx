import { Box, Chip, Grid, Typography } from '@mui/material'
import { motion } from 'framer-motion'
import { CloudUpload, SwipeRight, Recommend } from '@mui/icons-material'
import { SectionContainer, GlassCard } from '@/shared/components'
import { IntegrationOrbit } from './IntegrationOrbit'
import {
  fadeInUp,
  staggerContainer,
  slideInFromLeft,
  slideInFromRight,
} from '../../utils/animations'

const steps = [
  {
    id: 1,
    icon: <CloudUpload />,
    title: 'Upload Your Style',
    description: 'Share 2 outfit photos you love. Our AI analyzes your preferences instantly.',
  },
  {
    id: 2,
    icon: <SwipeRight />,
    title: 'Swipe to Train',
    description: 'Like or pass on 15 items. This helps our AI understand your taste better.',
  },
  {
    id: 3,
    icon: <Recommend />,
    title: 'Get Recommendations',
    description: 'Discover your perfect matches. Personalized suggestions tailored to you.',
  },
]

export const HowItWorks = () => {
  return (
    <Box
      component="section"
      sx={{
        bgcolor: '#f8f9fc',
      }}
    >
      <SectionContainer maxWidth="lg">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          variants={staggerContainer}
        >
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <motion.div variants={fadeInUp}>
              <Chip
                label="How It Works"
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
                Three simple steps to your perfect style
              </Typography>
            </motion.div>
            <motion.div variants={fadeInUp}>
              <Typography
                variant="body1"
                sx={{ color: 'text.secondary', maxWidth: 500, mx: 'auto' }}
              >
                Getting started is easy. Our AI does the heavy lifting so you can focus on looking
                great.
              </Typography>
            </motion.div>
          </Box>

          <Grid container spacing={6} alignItems="center">
            {/* Orbit Visual */}
            <Grid size={{ xs: 12, md: 5 }}>
              <motion.div variants={slideInFromLeft}>
                <IntegrationOrbit />
              </motion.div>
            </Grid>

            {/* Steps */}
            <Grid size={{ xs: 12, md: 7 }}>
              <motion.div variants={slideInFromRight}>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  {steps.map((step) => (
                    <GlassCard key={step.id} sx={{ display: 'flex', gap: 3, p: 3 }}>
                      <Box
                        sx={{
                          width: 56,
                          height: 56,
                          borderRadius: 2,
                          background:
                            'linear-gradient(135deg, rgba(91,74,228,0.1), rgba(123,107,240,0.1))',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0,
                          '& svg': {
                            fontSize: 28,
                            color: 'primary.main',
                          },
                        }}
                      >
                        {step.icon}
                      </Box>
                      <Box>
                        <Typography
                          variant="caption"
                          sx={{
                            color: 'primary.main',
                            fontWeight: 600,
                            textTransform: 'uppercase',
                            letterSpacing: 1,
                          }}
                        >
                          Step {step.id}
                        </Typography>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                          {step.title}
                        </Typography>
                        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                          {step.description}
                        </Typography>
                      </Box>
                    </GlassCard>
                  ))}
                </Box>
              </motion.div>
            </Grid>
          </Grid>
        </motion.div>
      </SectionContainer>
    </Box>
  )
}
