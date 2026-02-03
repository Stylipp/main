import { Box, Button, Container, Grid, Stack, Typography } from '@mui/material'
import { motion } from 'framer-motion'
import { ArrowForward } from '@mui/icons-material'
import { SwipeCards } from './SwipeCards'
import { LogoCarousel } from '../LogoCarousel'
import { fadeInUp, staggerContainer, slideInFromRight } from '../../utils/animations'

export const Hero = () => {
  return (
    <Box
      component="section"
      sx={{
        position: 'relative',
        height: { xs: 'auto', md: '100vh' },
        minHeight: { xs: 600, md: '100vh' },
        display: 'flex',
        alignItems: 'center',
        overflow: 'hidden',
        background: 'linear-gradient(180deg, #ffffff 0%, #f0f4ff 100%)',
        py: { xs: 6, md: 0 },
        mt: { xs: 0, md: '-64px' },
        pt: { xs: 6, md: '64px' },
      }}
    >
      <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
        <Grid container spacing={4} alignItems="center">
          {/* Left side - Text content */}
          <Grid size={{ xs: 12, md: 6 }}>
            <motion.div initial="hidden" animate="visible" variants={staggerContainer}>
              <Stack spacing={3} sx={{ maxWidth: 520 }}>
                <motion.div variants={fadeInUp}>
                  <Typography
                    variant="h1"
                    component="h1"
                    sx={{
                      color: 'text.primary',
                      fontWeight: 700,
                      fontSize: { xs: '2.5rem', md: '3.5rem' },
                      lineHeight: 1.1,
                    }}
                  >
                    Discover your perfect style.
                    <br />
                    <Box component="span" sx={{ color: 'primary.main' }}>
                      Swipe to match.
                    </Box>
                  </Typography>
                </motion.div>

                <motion.div variants={fadeInUp}>
                  <Typography
                    variant="body1"
                    sx={{
                      color: 'text.secondary',
                      fontSize: '1.125rem',
                      lineHeight: 1.7,
                    }}
                  >
                    Bring AI-powered styling to your wardrobe. Swipe through personalized
                    recommendations and build outfits you'll actually love.
                  </Typography>
                </motion.div>

                <motion.div variants={fadeInUp}>
                  <Button
                    variant="contained"
                    size="large"
                    endIcon={<ArrowForward />}
                    sx={{
                      bgcolor: 'primary.main',
                      color: 'white',
                      borderRadius: 2,
                      px: 4,
                      py: 1.5,
                      fontSize: '1rem',
                      fontWeight: 600,
                      '&:hover': {
                        bgcolor: 'primary.dark',
                      },
                    }}
                  >
                    Get Started
                  </Button>
                </motion.div>

                {/* Logo Carousel - under button */}
                <motion.div variants={fadeInUp}>
                  <Box sx={{ mt: 4 }}>
                    <LogoCarousel />
                  </Box>
                </motion.div>
              </Stack>
            </motion.div>
          </Grid>

          {/* Right side - Swipe cards */}
          <Grid size={{ xs: 12, md: 6 }}>
            <motion.div initial="hidden" animate="visible" variants={slideInFromRight}>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: { xs: 'center', md: 'flex-end' },
                  pt: { xs: 4, md: 0 },
                  pb: { xs: 8, md: 0 },
                }}
              >
                <SwipeCards />
              </Box>
            </motion.div>
          </Grid>
        </Grid>
      </Container>
    </Box>
  )
}
