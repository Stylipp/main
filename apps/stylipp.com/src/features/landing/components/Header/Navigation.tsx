import { useState } from 'react'
import { Box, Button, Paper, Popper, Typography, Fade } from '@mui/material'
import {
  KeyboardArrowDown as ArrowDownIcon,
  Explore,
  Checkroom,
  PlayCircleOutline,
  Article,
  MenuBook,
  Email,
} from '@mui/icons-material'

interface DropdownItem {
  label: string
  description: string
  href: string
  icon: React.ReactNode
}

interface NavItemWithDropdown {
  label: string
  href?: string
  children?: DropdownItem[]
}

const navItems: NavItemWithDropdown[] = [
  {
    label: 'Platform',
    children: [
      {
        label: 'Discover',
        description: 'Find your perfect style matches',
        href: '#discover',
        icon: <Explore />,
      },
      {
        label: 'Collections',
        description: 'Organize your wardrobe',
        href: '#collections',
        icon: <Checkroom />,
      },
      {
        label: 'How It Works',
        description: 'Learn about our AI styling',
        href: '#how-it-works',
        icon: <PlayCircleOutline />,
      },
    ],
  },
  {
    label: 'Resources',
    children: [
      {
        label: 'Blog',
        description: 'The latest posts and updates',
        href: '/blog',
        icon: <Article />,
      },
      {
        label: 'User documentation',
        description: 'Comprehensive guides for all',
        href: '/help',
        icon: <MenuBook />,
      },
      {
        label: 'Contact',
        description: 'Get in touch with our team',
        href: '/contact',
        icon: <Email />,
      },
    ],
  },
  { label: 'Careers', href: '/careers' },
]

interface NavigationProps {
  compact?: boolean
}

export const Navigation = ({ compact }: NavigationProps) => {
  const [openMenu, setOpenMenu] = useState<string | null>(null)
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null)

  const handleMouseEnter = (label: string, event: React.MouseEvent<HTMLElement>) => {
    setOpenMenu(label)
    setAnchorEl(event.currentTarget)
  }

  const handleMouseLeave = () => {
    setOpenMenu(null)
    setAnchorEl(null)
  }

  const isOpen = (label: string) => openMenu === label

  return (
    <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: compact ? 0 : 0.5 }}>
      {navItems.map((item) =>
        item.children ? (
          <Box
            key={item.label}
            onMouseEnter={(e) => handleMouseEnter(item.label, e)}
            onMouseLeave={handleMouseLeave}
          >
            <Button
              endIcon={
                <ArrowDownIcon
                  sx={{
                    fontSize: compact ? 16 : 18,
                    transition: 'transform 0.2s',
                    transform: isOpen(item.label) ? 'rotate(180deg)' : 'rotate(0)',
                  }}
                />
              }
              sx={{
                color: isOpen(item.label) ? 'primary.main' : 'text.primary',
                bgcolor: isOpen(item.label) ? 'rgba(91,74,228,0.08)' : 'transparent',
                borderRadius: 2,
                px: compact ? 1.5 : 2,
                py: compact ? 0.5 : 1,
                fontSize: compact ? '0.85rem' : '0.875rem',
                transition: 'all 0.3s ease',
                '&:hover': {
                  color: 'primary.main',
                  bgcolor: 'rgba(91,74,228,0.08)',
                },
              }}
            >
              {item.label}
            </Button>
            <Popper
              open={isOpen(item.label)}
              anchorEl={anchorEl}
              placement="bottom-start"
              transition
              sx={{ zIndex: 1300 }}
            >
              {({ TransitionProps }) => (
                <Fade {...TransitionProps} timeout={200}>
                  <Paper
                    sx={{
                      mt: 1,
                      p: 1,
                      minWidth: 280,
                      bgcolor: 'white',
                      border: '1px solid rgba(0,0,0,0.08)',
                      borderRadius: 3,
                      boxShadow: '0 10px 40px rgba(0,0,0,0.12)',
                    }}
                  >
                    {item.children?.map((child) => (
                      <Box
                        key={child.label}
                        component="a"
                        href={child.href}
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 2,
                          p: 1.5,
                          borderRadius: 2,
                          textDecoration: 'none',
                          transition: 'background 0.2s',
                          '&:hover': {
                            bgcolor: 'rgba(91,74,228,0.06)',
                          },
                        }}
                      >
                        <Box
                          sx={{
                            width: 40,
                            height: 40,
                            borderRadius: 2,
                            bgcolor: 'rgba(91,74,228,0.1)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            '& svg': {
                              fontSize: 20,
                              color: 'primary.main',
                            },
                          }}
                        >
                          {child.icon}
                        </Box>
                        <Box>
                          <Typography
                            variant="body2"
                            sx={{ fontWeight: 600, color: 'text.primary' }}
                          >
                            {child.label}
                          </Typography>
                          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                            {child.description}
                          </Typography>
                        </Box>
                      </Box>
                    ))}
                  </Paper>
                </Fade>
              )}
            </Popper>
          </Box>
        ) : (
          <Button
            key={item.label}
            href={item.href}
            sx={{
              color: 'text.primary',
              borderRadius: 2,
              px: compact ? 1.5 : 2,
              py: compact ? 0.5 : 1,
              fontSize: compact ? '0.85rem' : '0.875rem',
              transition: 'all 0.3s ease',
              '&:hover': {
                color: 'primary.main',
                bgcolor: 'rgba(91,74,228,0.08)',
              },
            }}
          >
            {item.label}
          </Button>
        )
      )}
    </Box>
  )
}
