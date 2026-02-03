import { useState } from 'react'
import {
  Box,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  Collapse,
  Divider,
} from '@mui/material'
import { Menu as MenuIcon, Close as CloseIcon, ExpandLess, ExpandMore } from '@mui/icons-material'
import { GradientButton } from '@/shared/components'

interface MobileDrawerProps {
  open: boolean
  onOpen: () => void
  onClose: () => void
}

const navItems = [
  {
    label: 'Platform',
    children: [
      { label: 'Discover', href: '#discover' },
      { label: 'Collections', href: '#collections' },
      { label: 'How It Works', href: '#how-it-works' },
    ],
  },
  {
    label: 'Resources',
    children: [
      { label: 'Blog', href: '/blog' },
      { label: 'Help Center', href: '/help' },
      { label: 'Contact', href: '/contact' },
    ],
  },
  { label: 'Blog', href: '/blog' },
]

export const MobileDrawer = ({ open, onOpen, onClose }: MobileDrawerProps) => {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  const toggleExpand = (label: string) => {
    setExpanded({ ...expanded, [label]: !expanded[label] })
  }

  return (
    <>
      <IconButton
        onClick={onOpen}
        sx={{ display: { xs: 'flex', md: 'none' }, color: 'text.primary' }}
        aria-label="Open menu"
      >
        <MenuIcon />
      </IconButton>

      <Drawer
        anchor="right"
        open={open}
        onClose={onClose}
        PaperProps={{
          sx: {
            width: 280,
            bgcolor: 'background.default',
            borderLeft: '1px solid rgba(0,0,0,0.1)',
          },
        }}
      >
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <IconButton onClick={onClose} sx={{ color: 'text.primary' }} aria-label="Close menu">
            <CloseIcon />
          </IconButton>
        </Box>

        <List sx={{ px: 2 }}>
          {navItems.map((item) =>
            item.children ? (
              <Box key={item.label}>
                <ListItemButton onClick={() => toggleExpand(item.label)}>
                  <ListItemText primary={item.label} sx={{ color: 'text.primary' }} />
                  {expanded[item.label] ? <ExpandLess /> : <ExpandMore />}
                </ListItemButton>
                <Collapse in={expanded[item.label]} timeout="auto" unmountOnExit>
                  <List component="div" disablePadding>
                    {item.children.map((child) => (
                      <ListItemButton
                        key={child.label}
                        component="a"
                        href={child.href}
                        sx={{ pl: 4 }}
                        onClick={onClose}
                      >
                        <ListItemText primary={child.label} sx={{ color: 'text.secondary' }} />
                      </ListItemButton>
                    ))}
                  </List>
                </Collapse>
              </Box>
            ) : (
              <ListItemButton key={item.label} component="a" href={item.href} onClick={onClose}>
                <ListItemText primary={item.label} sx={{ color: 'text.primary' }} />
              </ListItemButton>
            )
          )}
        </List>

        <Box sx={{ mt: 'auto', p: 2 }}>
          <Divider sx={{ mb: 2, borderColor: 'rgba(0,0,0,0.1)' }} />
          <GradientButton fullWidth sx={{ mb: 1 }}>
            Get Started
          </GradientButton>
        </Box>
      </Drawer>
    </>
  )
}
