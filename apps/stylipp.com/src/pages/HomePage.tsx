import { useTranslation } from 'react-i18next'
import Container from '@mui/material/Container'
import Typography from '@mui/material/Typography'
import Box from '@mui/material/Box'

export default function HomePage() {
  const { t } = useTranslation()

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, textAlign: 'center' }}>
        <Typography variant="h3" component="h1" gutterBottom>
          {t('app.name')}
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" gutterBottom>
          {t('app.tagline')}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome to Stylipp. Your personalized fashion discovery starts here.
        </Typography>
      </Box>
    </Container>
  )
}
