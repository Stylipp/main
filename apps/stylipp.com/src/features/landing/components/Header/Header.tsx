import { useState } from 'react'
import { AppBar, Box, Button, Toolbar, Typography, useScrollTrigger } from '@mui/material'
import { motion, AnimatePresence } from 'framer-motion'
import { Navigation } from './Navigation'
import { MobileDrawer } from './MobileDrawer'
import { AnnouncementBanner } from './AnnouncementBanner'

export const Header = () => {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [bannerDismissed, setBannerDismissed] = useState(false)

  const trigger = useScrollTrigger({
    disableHysteresis: true,
    threshold: 50,
  })

  const showBanner = !trigger && !bannerDismissed

  return (
    <Box sx={{ position: 'sticky', top: 0, zIndex: 1100 }}>
      {/* Announcement Banner - hides on scroll */}
      <AnimatePresence>
        {showBanner && (
          <motion.div
            initial={{ height: 'auto', opacity: 1 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            style={{ overflow: 'hidden' }}
          >
            <AnnouncementBanner onDismiss={() => setBannerDismissed(true)} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Header */}
      <Box
        component={motion.div}
        animate={{
          padding: trigger ? '12px 24px' : '0px',
        }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        sx={{
          bgcolor: trigger ? 'transparent' : 'rgba(255,255,255,0.95)',
        }}
      >
        <AppBar
          position="static"
          component={motion.header}
          animate={{
            borderRadius: trigger ? 100 : 0,
            margin: trigger ? '0 auto' : 0,
          }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
          sx={{
            backdropFilter: 'blur(16px)',
            backgroundColor: trigger ? 'rgba(255,255,255,0.98)' : 'rgba(255,255,255,0.8)',
            boxShadow: trigger ? '0 2px 24px rgba(0,0,0,0.08)' : 'none',
            maxWidth: trigger ? 720 : '100%',
            mx: 'auto',
            border: trigger ? '1px solid rgba(0,0,0,0.06)' : 'none',
          }}
        >
          <Toolbar
            component={motion.div}
            animate={{
              paddingTop: trigger ? 12 : 8,
              paddingBottom: trigger ? 12 : 8,
              paddingLeft: trigger ? 24 : 24,
              paddingRight: trigger ? 24 : 24,
            }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            sx={{
              justifyContent: 'space-between',
              width: '100%',
              minHeight: 'auto !important',
            }}
          >
            {/* Logo */}
            <Box
              component="a"
              href="/"
              sx={{ display: 'flex', alignItems: 'center', gap: 1, textDecoration: 'none' }}
            >
              <Box
                component={motion.div}
                animate={{
                  width: trigger ? 32 : 36,
                  height: trigger ? 32 : 36,
                }}
                transition={{ duration: 0.3 }}
                sx={{
                  borderRadius: 1.5,
                  background: 'linear-gradient(135deg, #5B4AE4 0%, #7B6BF0 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Typography
                  sx={{ color: 'white', fontWeight: 700, fontSize: trigger ? '1rem' : '1.1rem' }}
                >
                  S
                </Typography>
              </Box>
              <AnimatePresence>
                {!trigger && (
                  <motion.div
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: 'auto' }}
                    exit={{ opacity: 0, width: 0 }}
                    transition={{ duration: 0.2 }}
                    style={{ overflow: 'hidden', whiteSpace: 'nowrap' }}
                  >
                    <Typography
                      variant="h6"
                      sx={{
                        fontWeight: 700,
                        color: 'text.primary',
                        fontSize: '1.25rem',
                      }}
                    >
                      stylipp
                    </Typography>
                  </motion.div>
                )}
              </AnimatePresence>
            </Box>

            {/* Desktop Navigation */}
            <Navigation compact={trigger} />

            {/* Right CTAs */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: trigger ? 1 : 1.5 }}>
              <Button
                sx={{
                  display: { xs: 'none', md: 'inline-flex' },
                  color: 'text.primary',
                  border: '1px solid rgba(0,0,0,0.12)',
                  borderRadius: trigger ? 6 : 2,
                  px: trigger ? 2 : 2.5,
                  py: trigger ? 0.75 : 1,
                  fontSize: trigger ? '0.8rem' : '0.875rem',
                  fontWeight: 500,
                  textTransform: 'none',
                  transition: 'all 0.3s ease',
                  '&:hover': { bgcolor: 'rgba(0,0,0,0.04)' },
                }}
              >
                Log in
              </Button>
              <Button
                variant="contained"
                sx={{
                  display: { xs: 'none', md: 'inline-flex' },
                  bgcolor: 'primary.main',
                  color: 'white',
                  borderRadius: trigger ? 6 : 2,
                  px: trigger ? 2 : 2.5,
                  py: trigger ? 0.75 : 1,
                  fontSize: trigger ? '0.8rem' : '0.875rem',
                  fontWeight: 500,
                  textTransform: 'none',
                  transition: 'all 0.3s ease',
                  boxShadow: 'none',
                  '&:hover': { bgcolor: 'primary.dark', boxShadow: 'none' },
                }}
              >
                Book a demo
              </Button>

              {/* Mobile Menu */}
              <MobileDrawer
                open={drawerOpen}
                onOpen={() => setDrawerOpen(true)}
                onClose={() => setDrawerOpen(false)}
              />
            </Box>
          </Toolbar>
        </AppBar>
      </Box>
    </Box>
  )
}
