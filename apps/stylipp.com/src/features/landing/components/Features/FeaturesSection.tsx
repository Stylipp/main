import { Box, Container, Grid, Typography } from '@mui/material'
import { motion } from 'framer-motion'
import { AutoAwesome, Checkroom, StyleOutlined, TrendingUp } from '@mui/icons-material'
import { FeatureCard } from './FeatureCard'
import { fadeInUp, staggerContainer } from '../../utils/animations'
import type { Feature } from '../../types/landing.types'

const features: Feature[] = [
  {
    id: '1',
    icon: <AutoAwesome />,
    title: 'Personal Styling',
    description:
      'Get AI-powered outfit recommendations tailored to your unique style preferences and body type.',
  },
  {
    id: '2',
    icon: <Checkroom />,
    title: 'Wardrobe Management',
    description:
      'Organize and track your clothes. Build collections for any occasion and never wonder what to wear.',
  },
  {
    id: '3',
    icon: <StyleOutlined />,
    title: 'Style Discovery',
    description:
      'Explore new trends and discover pieces that match your aesthetic. Expand your fashion horizons.',
  },
  {
    id: '4',
    icon: <TrendingUp />,
    title: 'Smart Recommendations',
    description:
      'Our AI learns from your choices and continuously improves suggestions to match your evolving taste.',
  },
]

export const FeaturesSection = () => {
  return (
    <Box
      component="section"
      sx={{
        py: { xs: 8, md: 12 },
        bgcolor: '#fafbfc',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Background decoration */}
      <Box
        sx={{
          position: 'absolute',
          top: -200,
          right: -200,
          width: 500,
          height: 500,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(91,74,228,0.03) 0%, transparent 70%)',
          pointerEvents: 'none',
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          bottom: -150,
          left: -150,
          width: 400,
          height: 400,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(123,107,240,0.04) 0%, transparent 70%)',
          pointerEvents: 'none',
        }}
      />

      <Container maxWidth="lg" sx={{ position: 'relative' }}>
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          variants={staggerContainer}
        >
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <motion.div variants={fadeInUp}>
              <Typography
                component="span"
                sx={{
                  display: 'inline-block',
                  px: 2.5,
                  py: 0.75,
                  mb: 3,
                  borderRadius: 6,
                  bgcolor: 'rgba(91,74,228,0.08)',
                  color: 'primary.main',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  letterSpacing: '0.02em',
                }}
              >
                Features
              </Typography>
            </motion.div>
            <motion.div variants={fadeInUp}>
              <Typography
                variant="h2"
                sx={{
                  mb: 2.5,
                  fontWeight: 800,
                  fontSize: { xs: '2rem', md: '2.75rem' },
                  background: 'linear-gradient(135deg, #1a1a2e 0%, #5B4AE4 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                }}
              >
                AI agents built to automate your styling
              </Typography>
            </motion.div>
            <motion.div variants={fadeInUp}>
              <Typography
                variant="body1"
                sx={{
                  color: 'text.secondary',
                  maxWidth: 550,
                  mx: 'auto',
                  fontSize: '1.1rem',
                  lineHeight: 1.7,
                }}
              >
                Discover how our intelligent styling assistant transforms your fashion experience
                with cutting-edge AI technology.
              </Typography>
            </motion.div>
          </Box>

          <Grid container spacing={3}>
            {features.map((feature, index) => (
              <Grid size={{ xs: 12, sm: 6, md: 3 }} key={feature.id}>
                <FeatureCard feature={feature} index={index} />
              </Grid>
            ))}
          </Grid>
        </motion.div>
      </Container>
    </Box>
  )
}
