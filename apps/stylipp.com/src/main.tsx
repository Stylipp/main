import { StrictMode, Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import { ThemeProvider } from '@mui/material/styles'
import { HelmetProvider } from 'react-helmet-async'
import CssBaseline from '@mui/material/CssBaseline'
import theme from './theme'
import App from './App'
import LoadingFallback from './components/LoadingFallback'

import './i18n'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <HelmetProvider>
      <Suspense fallback={<LoadingFallback />}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <App />
        </ThemeProvider>
      </Suspense>
    </HelmetProvider>
  </StrictMode>
)
