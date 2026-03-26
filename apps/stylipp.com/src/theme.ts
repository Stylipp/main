import { createTheme } from '@mui/material/styles'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#5B4AE4',
      light: '#7B6BF0',
      dark: '#4338CA',
    },
    secondary: {
      main: '#EC4899',
      light: '#F472B6',
      dark: '#DB2777',
    },
    background: {
      default: '#FAFAFA',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#1a1a2e',
      secondary: '#64748b',
    },
    success: {
      main: '#22C55E',
      dark: '#16A34A',
    },
    error: {
      main: '#EF4444',
      dark: '#DC2626',
    },
  },
  typography: {
    fontFamily: '"Manrope", "Inter", "Roboto", sans-serif',
    h1: {
      fontFamily: '"Syne", "Manrope", sans-serif',
      fontWeight: 700,
      fontSize: '3.5rem',
      lineHeight: 1.1,
      '@media (max-width:600px)': {
        fontSize: '2.25rem',
      },
    },
    h2: {
      fontFamily: '"Syne", "Manrope", sans-serif',
      fontWeight: 700,
      fontSize: '2.5rem',
      '@media (max-width:600px)': {
        fontSize: '1.75rem',
      },
    },
    h3: {
      fontFamily: '"Syne", "Manrope", sans-serif',
      fontWeight: 600,
      fontSize: '1.75rem',
    },
    h5: {
      fontWeight: 400,
      fontSize: '1.25rem',
      color: 'rgba(255,255,255,0.7)',
    },
    h6: {
      fontFamily: '"Syne", "Manrope", sans-serif',
      fontWeight: 700,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 12,
          fontWeight: 600,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          background: '#ffffff',
          boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
          border: '1px solid rgba(0,0,0,0.06)',
        },
      },
    },
  },
})

export default theme
