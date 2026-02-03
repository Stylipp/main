import { Box } from '@mui/material'
import { Helmet } from 'react-helmet-async'
import { Header } from '../components/Header'
import { Hero } from '../components/Hero'
import { FeaturesSection } from '../components/Features'
import { HowItWorks } from '../components/HowItWorks'
import { BenefitsSection } from '../components/Benefits'
import { TestimonialsSection } from '../components/Testimonials'
import { CTASection } from '../components/CTA'
import { Footer } from '../components/Footer'

export const LandingPage = () => {
  return (
    <>
      <Helmet>
        <title>Stylipp - AI Personal Stylist | Discover Your Perfect Look</title>
        <meta
          name="description"
          content="Get personalized fashion recommendations powered by AI. Upload your style, swipe to train, and discover clothes you'll love."
        />
        <meta property="og:title" content="Stylipp - AI Personal Stylist" />
        <meta
          property="og:description"
          content="Discover your perfect look with AI-powered styling"
        />
        <meta property="og:type" content="website" />
        <meta name="twitter:card" content="summary_large_image" />
      </Helmet>

      <Box sx={{ bgcolor: '#ffffff', minHeight: '100vh' }}>
        <Header />
        <Hero />
        <FeaturesSection />
        <HowItWorks />
        <BenefitsSection />
        <TestimonialsSection />
        <CTASection />
        <Footer />
      </Box>
    </>
  )
}
