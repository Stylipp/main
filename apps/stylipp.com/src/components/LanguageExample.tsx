import { useTranslation } from 'react-i18next'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'

export default function LanguageExample() {
  const { t } = useTranslation()

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4" gutterBottom>
        {t('app.name')}
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        {t('app.tagline')}
      </Typography>
      <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
        <Button variant="contained">{t('common.save')}</Button>
        <Button variant="outlined">{t('common.cancel')}</Button>
      </Box>
    </Box>
  )
}
