import { Box, Button, Typography } from '@mui/material'
import { motion } from 'framer-motion'
import { SectionContainer } from '@/shared/components'
import { fadeInUp, staggerContainer } from '../../utils/animations'

export const CTASection = () => {
  return (
    <SectionContainer component="section" maxWidth="lg">
      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-100px' }}
        variants={staggerContainer}
      >
        <Box
          sx={{
            background: 'linear-gradient(135deg, #5B4AE4, #7B6BF0)',
            borderRadius: 4,
            py: { xs: 6, md: 8 },
            px: { xs: 3, md: 6 },
            textAlign: 'center',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Background glow effect */}
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: 400,
              height: 400,
              borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(255,255,255,0.2), transparent)',
              filter: 'blur(60px)',
              pointerEvents: 'none',
            }}
          />

          <Box sx={{ position: 'relative', zIndex: 1 }}>
            <motion.div variants={fadeInUp}>
              <Typography variant="h2" sx={{ mb: 2, color: 'white' }}>
                Ready to Transform Your Style?
              </Typography>
            </motion.div>

            <motion.div variants={fadeInUp}>
              <Typography
                variant="body1"
                sx={{
                  color: 'rgba(255,255,255,0.8)',
                  maxWidth: 500,
                  mx: 'auto',
                  mb: 4,
                }}
              >
                Join thousands of users who have discovered their perfect style with Stylipp's
                AI-powered recommendations.
              </Typography>
            </motion.div>

            <motion.div variants={fadeInUp}>
              <Button
                size="large"
                sx={{
                  px: 5,
                  py: 1.5,
                  fontSize: '1.1rem',
                  bgcolor: 'white',
                  color: 'primary.main',
                  fontWeight: 600,
                  borderRadius: 2,
                  '&:hover': {
                    bgcolor: 'rgba(255,255,255,0.9)',
                  },
                }}
              >
                Get Started Free
              </Button>
            </motion.div>

            <motion.div variants={fadeInUp}>
              <Typography
                variant="caption"
                sx={{
                  display: 'block',
                  mt: 2,
                  color: 'rgba(255,255,255,0.7)',
                }}
              >
                No credit card required • Free forever for basic features
              </Typography>
            </motion.div>
          </Box>
        </Box>
      </motion.div>
    </SectionContainer>
  )
}
