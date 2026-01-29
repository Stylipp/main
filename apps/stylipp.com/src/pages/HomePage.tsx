import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';

export default function HomePage() {
  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, textAlign: 'center' }}>
        <Typography variant="h3" component="h1" gutterBottom>
          Stylipp - AI Personal Stylist
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome to Stylipp. Your personalized fashion discovery starts here.
        </Typography>
      </Box>
    </Container>
  );
}
