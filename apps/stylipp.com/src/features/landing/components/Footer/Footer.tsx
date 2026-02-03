import {
  Box,
  Container,
  Divider,
  Grid,
  IconButton,
  Link,
  TextField,
  Typography,
} from '@mui/material'
import { Instagram, Twitter, LinkedIn, Send } from '@mui/icons-material'
import { GradientButton } from '@/shared/components'

const footerLinks = {
  platform: [
    { label: 'Discover', href: '#discover' },
    { label: 'Collections', href: '#collections' },
    { label: 'How It Works', href: '#how-it-works' },
  ],
  resources: [
    { label: 'Blog', href: '/blog' },
    { label: 'Help Center', href: '/help' },
    { label: 'Contact', href: '/contact' },
  ],
  legal: [
    { label: 'Privacy Policy', href: '/privacy' },
    { label: 'Terms of Service', href: '/terms' },
  ],
}

const socialLinks = [
  { Icon: Instagram, href: 'https://instagram.com', label: 'Instagram' },
  { Icon: Twitter, href: 'https://twitter.com', label: 'Twitter' },
  { Icon: LinkedIn, href: 'https://linkedin.com', label: 'LinkedIn' },
]

export const Footer = () => {
  return (
    <Box
      component="footer"
      sx={{
        bgcolor: '#f8f9fc',
        borderTop: '1px solid rgba(0,0,0,0.06)',
        pt: 8,
        pb: 4,
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={4}>
          {/* Platform Links */}
          <Grid size={{ xs: 6, sm: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2, color: 'text.primary' }}>
              Platform
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {footerLinks.platform.map((link) => (
                <Link
                  key={link.label}
                  href={link.href}
                  sx={{
                    color: 'text.secondary',
                    textDecoration: 'none',
                    fontSize: '0.875rem',
                    '&:hover': { color: 'primary.main' },
                  }}
                >
                  {link.label}
                </Link>
              ))}
            </Box>
          </Grid>

          {/* Resources Links */}
          <Grid size={{ xs: 6, sm: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2, color: 'text.primary' }}>
              Resources
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {footerLinks.resources.map((link) => (
                <Link
                  key={link.label}
                  href={link.href}
                  sx={{
                    color: 'text.secondary',
                    textDecoration: 'none',
                    fontSize: '0.875rem',
                    '&:hover': { color: 'primary.main' },
                  }}
                >
                  {link.label}
                </Link>
              ))}
            </Box>
          </Grid>

          {/* Legal Links */}
          <Grid size={{ xs: 6, sm: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2, color: 'text.primary' }}>
              Legal
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {footerLinks.legal.map((link) => (
                <Link
                  key={link.label}
                  href={link.href}
                  sx={{
                    color: 'text.secondary',
                    textDecoration: 'none',
                    fontSize: '0.875rem',
                    '&:hover': { color: 'primary.main' },
                  }}
                >
                  {link.label}
                </Link>
              ))}
            </Box>
          </Grid>

          {/* Newsletter */}
          <Grid size={{ xs: 12, sm: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2, color: 'text.primary' }}>
              Stay in the loop
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
              Get the latest style tips and updates.
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                size="small"
                placeholder="Enter your email"
                sx={{
                  flex: 1,
                  '& .MuiOutlinedInput-root': {
                    bgcolor: 'white',
                    '& fieldset': {
                      borderColor: 'rgba(0,0,0,0.15)',
                    },
                    '&:hover fieldset': {
                      borderColor: 'rgba(0,0,0,0.25)',
                    },
                  },
                  '& input': {
                    color: 'text.primary',
                    fontSize: '0.875rem',
                  },
                }}
              />
              <GradientButton sx={{ minWidth: 'auto', px: 2 }} aria-label="Subscribe">
                <Send sx={{ fontSize: 18 }} />
              </GradientButton>
            </Box>
          </Grid>
        </Grid>

        <Divider sx={{ my: 4, borderColor: 'rgba(0,0,0,0.1)' }} />

        {/* Bottom Bar */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <Typography
            variant="body2"
            sx={{
              color: 'text.secondary',
              textAlign: { xs: 'center', sm: 'left' },
            }}
          >
            © 2026 Stylipp. All rights reserved.
          </Typography>

          <Box sx={{ display: 'flex', gap: 1 }}>
            {socialLinks.map(({ Icon, href, label }) => (
              <IconButton
                key={label}
                component="a"
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                size="small"
                sx={{
                  color: 'text.secondary',
                  '&:hover': {
                    color: 'primary.main',
                    bgcolor: 'rgba(0,0,0,0.04)',
                  },
                }}
                aria-label={label}
              >
                <Icon fontSize="small" />
              </IconButton>
            ))}
          </Box>
        </Box>
      </Container>
    </Box>
  )
}
