# Stylipp Homepage - Development Tasks

> Based on [tildei.com](https://www.tildei.com/) design patterns  
> **Project:** Stylipp - AI Personal Stylist Platform  
> **Page:** Homepage (Marketing/Landing Page)  
> **Location:** `apps/web/src/features/landing/`

---

## 🎯 Overview

The homepage is a marketing landing page for Stylipp, following the Tildei.com design:
- Dark theme aesthetic with gradient accents
- Smooth scroll animations (Framer Motion)
- Logo carousel for social proof
- Testimonial cards
- Clear CTAs leading to onboarding

---

## Phase 1: Feature Setup

### 1.1 Create Landing Feature Structure
```
apps/web/src/features/landing/
├── api/                    # (minimal - mostly static page)
├── components/
│   ├── Header/
│   │   ├── Header.tsx
│   │   ├── Navigation.tsx
│   │   ├── MobileDrawer.tsx
│   │   └── AnnouncementBanner.tsx
│   ├── Hero/
│   │   ├── Hero.tsx
│   │   └── HeroVisual.tsx
│   ├── LogoCarousel/
│   │   └── LogoCarousel.tsx
│   ├── Features/
│   │   ├── FeaturesSection.tsx
│   │   └── FeatureCard.tsx
│   ├── HowItWorks/
│   │   ├── HowItWorks.tsx
│   │   └── IntegrationOrbit.tsx
│   ├── Benefits/
│   │   └── BenefitsSection.tsx
│   ├── Testimonials/
│   │   ├── TestimonialsSection.tsx
│   │   └── TestimonialCard.tsx
│   ├── CTA/
│   │   └── CTASection.tsx
│   └── Footer/
│       └── Footer.tsx
├── pages/
│   └── LandingPage.tsx
├── routes/
│   └── index.tsx
├── types/
│   └── landing.types.ts
└── utils/
    └── animations.ts
```

- [ ] Create feature folder structure
- [ ] Create `landing.types.ts` with interfaces
- [ ] Create `animations.ts` with Framer Motion variants

### 1.2 Landing Page Types
```typescript
// apps/web/src/features/landing/types/landing.types.ts

export interface NavItem {
  label: string;
  href?: string;
  children?: NavItem[];
}

export interface Testimonial {
  id: string;
  companyLogo: string;
  companyName: string;
  quote: string;
  fullText: string;
  authorName: string;
  authorRole: string;
}

export interface Feature {
  id: string;
  icon: React.ReactNode;
  title: string;
  description: string;
}

export interface Benefit {
  id: string;
  icon: React.ReactNode;
  title: string;
  description: string;
}

export interface PartnerLogo {
  id: string;
  name: string;
  src: string;
}
```

### 1.3 Animation Utilities
```typescript
// apps/web/src/features/landing/utils/animations.ts
import { Variants } from 'framer-motion';

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 40 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.6, ease: 'easeOut' }
  }
};

export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

export const scaleOnHover = {
  whileHover: { scale: 1.02 },
  whileTap: { scale: 0.98 }
};
```

---

## Phase 2: Shared Components Setup

### 2.1 Theme Extension
Location: `apps/web/src/shared/theme/`

- [ ] Extend MUI theme with landing page styles:
```typescript
// apps/web/src/shared/theme/theme.ts
import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#8B5CF6',      // Purple
      light: '#A78BFA',
      dark: '#7C3AED',
    },
    secondary: {
      main: '#EC4899',      // Pink
      light: '#F472B6',
      dark: '#DB2777',
    },
    background: {
      default: '#0a0a0f',
      paper: '#12121a',
    },
    text: {
      primary: '#ffffff',
      secondary: 'rgba(255,255,255,0.7)',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
      fontSize: '3.5rem',
      lineHeight: 1.1,
      '@media (max-width:600px)': {
        fontSize: '2.25rem',
      },
    },
    h2: {
      fontWeight: 700,
      fontSize: '2.5rem',
      '@media (max-width:600px)': {
        fontSize: '1.75rem',
      },
    },
    h3: {
      fontWeight: 600,
      fontSize: '1.75rem',
    },
    h5: {
      fontWeight: 400,
      fontSize: '1.25rem',
      color: 'rgba(255,255,255,0.7)',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
          fontWeight: 600,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          background: 'rgba(255,255,255,0.03)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255,255,255,0.1)',
        },
      },
    },
  },
});
```

### 2.2 Shared UI Components
Location: `apps/web/src/shared/components/`

- [ ] Create `GradientButton.tsx`:
```typescript
// apps/web/src/shared/components/GradientButton.tsx
import { Button, ButtonProps, styled } from '@mui/material';

export const GradientButton = styled(Button)<ButtonProps>(({ theme }) => ({
  background: 'linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%)',
  color: '#fff',
  padding: '12px 32px',
  '&:hover': {
    background: 'linear-gradient(135deg, #7C3AED 0%, #DB2777 100%)',
  },
}));
```

- [ ] Create `GradientText.tsx`:
```typescript
// apps/web/src/shared/components/GradientText.tsx
import { Typography, TypographyProps, styled } from '@mui/material';

export const GradientText = styled(Typography)<TypographyProps>(() => ({
  background: 'linear-gradient(135deg, #fff 0%, #8B5CF6 50%, #EC4899 100%)',
  backgroundClip: 'text',
  WebkitBackgroundClip: 'text',
  color: 'transparent',
}));
```

- [ ] Create `GlassCard.tsx`:
```typescript
// apps/web/src/shared/components/GlassCard.tsx
import { Card, CardProps, styled } from '@mui/material';

export const GlassCard = styled(Card)<CardProps>(() => ({
  background: 'rgba(255,255,255,0.03)',
  backdropFilter: 'blur(10px)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: 16,
}));
```

- [ ] Create `SectionContainer.tsx`:
```typescript
// apps/web/src/shared/components/SectionContainer.tsx
import { Container, ContainerProps, styled } from '@mui/material';

export const SectionContainer = styled(Container)<ContainerProps>(() => ({
  paddingTop: 80,
  paddingBottom: 80,
  '@media (max-width:600px)': {
    paddingTop: 48,
    paddingBottom: 48,
  },
}));
```

- [ ] Create `AnimatedBox.tsx` (Framer Motion wrapper)

---

## Phase 3: Header & Navigation

### 3.1 Announcement Banner
Location: `apps/web/src/features/landing/components/Header/AnnouncementBanner.tsx`

- [ ] Create gradient background banner
- [ ] Add `<Chip>` for badge/award
- [ ] Add announcement text with `<Typography>`
- [ ] Add "Learn More" `<Link>` with arrow icon
- [ ] Add optional dismiss `<IconButton>`
- [ ] Add Framer Motion slide-down animation

### 3.2 Main Header
Location: `apps/web/src/features/landing/components/Header/Header.tsx`

- [ ] Create sticky `<AppBar>` with backdrop blur:
  ```tsx
  <AppBar 
    position="sticky" 
    sx={{
      backdropFilter: 'blur(10px)',
      backgroundColor: 'rgba(10,10,15,0.8)',
      boxShadow: 'none',
    }}
  >
  ```
- [ ] Add `<Toolbar>` with 3 sections:
  - Left: Logo
  - Center: Navigation links
  - Right: CTAs (Login + Get Started)
- [ ] Implement `useScrollTrigger` for header elevation change

### 3.3 Navigation Component
Location: `apps/web/src/features/landing/components/Header/Navigation.tsx`

- [ ] Create nav links with `<Button>`:
  - Platform (dropdown)
  - Resources (dropdown)
  - Blog
- [ ] Implement dropdown menus with `<Menu>` + `<MenuItem>`
- [ ] Add hover animations

### 3.4 Mobile Drawer
Location: `apps/web/src/features/landing/components/Header/MobileDrawer.tsx`

- [ ] Create hamburger `<IconButton>` (visible only on mobile)
- [ ] Implement `<Drawer>` with navigation links
- [ ] Add accordion for nested menu items
- [ ] Add CTAs at bottom of drawer

---

## Phase 4: Hero Section

### 4.1 Hero Content
Location: `apps/web/src/features/landing/components/Hero/Hero.tsx`

- [ ] Create section with centered content
- [ ] Add main headline with `<GradientText variant="h1">`:
  > "AI-Powered Personal Styling. Discover Your Perfect Look."
- [ ] Add subheadline `<Typography variant="h5">`:
  > "Get personalized fashion recommendations that match your unique style."
- [ ] Add CTA buttons with `<Stack direction="row" spacing={2}>`:
  - Primary: `<GradientButton>` → "Get Started Free"
  - Secondary: `<Button variant="outlined">` → "Watch Demo"
- [ ] Implement staggered entrance animations with Framer Motion

### 4.2 Hero Visual
Location: `apps/web/src/features/landing/components/Hero/HeroVisual.tsx`

- [ ] Create gradient orb background effect:
  ```tsx
  <Box sx={{
    position: 'absolute',
    width: 500,
    height: 500,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(139,92,246,0.3), transparent)',
    filter: 'blur(80px)',
    zIndex: -1,
  }} />
  ```
- [ ] Optional: Add floating mockup images

---

## Phase 5: Social Proof - Logo Carousel

### 5.1 Logo Carousel
Location: `apps/web/src/features/landing/components/LogoCarousel/LogoCarousel.tsx`

- [ ] Create infinite scroll container
- [ ] Implement CSS keyframes animation:
  ```tsx
  const marqueeAnimation = keyframes`
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
  `;
  ```
- [ ] Add partner/brand logos (8-12 logos)
- [ ] Duplicate logos for seamless loop
- [ ] Apply grayscale filter with opacity
- [ ] Optional: Two rows scrolling in opposite directions
- [ ] Pause animation on hover for accessibility

---

## Phase 6: Features Section

### 6.1 Section Header
Location: `apps/web/src/features/landing/components/Features/FeaturesSection.tsx`

- [ ] Add section label `<Chip label="Features" />`
- [ ] Add heading: "AI agents built to automate your styling"
- [ ] Add description paragraph

### 6.2 Feature Cards
Location: `apps/web/src/features/landing/components/Features/FeatureCard.tsx`

- [ ] Create interactive tabs or toggle buttons
- [ ] Implement `<GlassCard>` for each feature:

**Feature 1: Personal Styling**
- Icon: `<AutoAwesome />` or similar
- Title: "Personal Styling"
- Description: "Get AI-powered outfit recommendations tailored to your unique style preferences."

**Feature 2: Wardrobe Management**
- Icon: `<Checkroom />` or similar
- Title: "Wardrobe Management"
- Description: "Organize and track your clothes. Build collections for any occasion."

- [ ] Add Framer Motion `<AnimatePresence>` for tab transitions
- [ ] Add visual/illustration for active feature

---

## Phase 7: How It Works Section

### 7.1 Section Layout
Location: `apps/web/src/features/landing/components/HowItWorks/HowItWorks.tsx`

- [ ] Add section heading: "How Stylipp Works"
- [ ] Add subheading explaining the 3-step process

### 7.2 Integration Orbit Visual
Location: `apps/web/src/features/landing/components/HowItWorks/IntegrationOrbit.tsx`

- [ ] Create central circle with gradient border
- [ ] Add orbiting integration icons:
  - Instagram
  - Pinterest
  - Shopping bag
  - AI/ML badge
- [ ] Implement CSS or Framer Motion orbit animation
- [ ] Add connection lines (optional)
- [ ] Add noise texture overlay

### 7.3 Steps Explanation
- [ ] Create 3 step cards:
  1. **Upload Your Style** - Share 2 outfit photos you love
  2. **Swipe to Train** - Like or pass on 15 items
  3. **Get Recommendations** - Discover your perfect matches

---

## Phase 8: Benefits Section

### 8.1 Benefits Grid
Location: `apps/web/src/features/landing/components/Benefits/BenefitsSection.tsx`

- [ ] Create `<Grid container spacing={4}>`
- [ ] Add 4 benefit items:

| Benefit | Icon | Description |
|---------|------|-------------|
| **Continuously Learning** | `<Psychology />` | Evolves with your style preferences |
| **24/7 Available** | `<AccessTime />` | Get styling advice anytime |
| **Multilingual** | `<Translate />` | Supports Hebrew and English |
| **Personalized** | `<PersonOutline />` | Tailored to your body type |

- [ ] Style with subtle card background
- [ ] Add entrance animations

---

## Phase 9: Testimonials Section

### 9.1 Section Header
Location: `apps/web/src/features/landing/components/Testimonials/TestimonialsSection.tsx`

- [ ] Add `<Chip label="Testimonials" />`
- [ ] Add heading: "Why Users Love Stylipp"
- [ ] Add intro paragraph

### 9.2 Testimonial Carousel
- [ ] Implement Embla Carousel:
  ```tsx
  const [emblaRef] = useEmblaCarousel({ 
    loop: true, 
    align: 'start',
    slidesToScroll: 1 
  });
  ```
- [ ] Create navigation dots or arrows
- [ ] Add auto-play with pause on hover

### 9.3 Testimonial Card
Location: `apps/web/src/features/landing/components/Testimonials/TestimonialCard.tsx`

- [ ] Create `<GlassCard>` with:
  - Company/user avatar or logo
  - Highlighted quote (short)
  - Full testimonial text
  - Author name
  - Author role/description
- [ ] Add hover effect

---

## Phase 10: CTA Section

### 10.1 CTA Block
Location: `apps/web/src/features/landing/components/CTA/CTASection.tsx`

- [ ] Create full-width section with gradient background:
  ```tsx
  sx={{
    background: 'linear-gradient(135deg, rgba(139,92,246,0.2), rgba(236,72,153,0.2))',
    borderRadius: 4,
    py: 8,
    textAlign: 'center',
  }}
  ```
- [ ] Add compelling headline: "Ready to Transform Your Style?"
- [ ] Add `<GradientButton size="large">` → "Get Started Free"
- [ ] Optional: Add trust badges or stats

---

## Phase 11: Footer

### 11.1 Footer Structure
Location: `apps/web/src/features/landing/components/Footer/Footer.tsx`

- [ ] Create `<Box component="footer">` with dark background
- [ ] Add `<Grid container>` with columns:

**Column 1: Platform**
- Discover
- Collections
- How It Works

**Column 2: Resources**
- Blog
- Help Center
- Contact

**Column 3: Legal**
- Privacy Policy
- Terms of Service

**Column 4: Newsletter**
- "Stay in the loop" text
- Email `<TextField>`
- Submit `<Button>`

- [ ] Add `<Divider>`
- [ ] Add bottom bar with:
  - Copyright: "© 2026 Stylipp. All rights reserved."
  - Social links (optional)

---

## Phase 12: Landing Page Assembly

### 12.1 Create LandingPage
Location: `apps/web/src/features/landing/pages/LandingPage.tsx`

```typescript
// apps/web/src/features/landing/pages/LandingPage.tsx
import { Box } from '@mui/material';
import { Header } from '../components/Header/Header';
import { Hero } from '../components/Hero/Hero';
import { LogoCarousel } from '../components/LogoCarousel/LogoCarousel';
import { FeaturesSection } from '../components/Features/FeaturesSection';
import { HowItWorks } from '../components/HowItWorks/HowItWorks';
import { BenefitsSection } from '../components/Benefits/BenefitsSection';
import { TestimonialsSection } from '../components/Testimonials/TestimonialsSection';
import { CTASection } from '../components/CTA/CTASection';
import { Footer } from '../components/Footer/Footer';

export const LandingPage = () => {
  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100vh' }}>
      <Header />
      <Hero />
      <LogoCarousel />
      <FeaturesSection />
      <HowItWorks />
      <BenefitsSection />
      <TestimonialsSection />
      <CTASection />
      <Footer />
    </Box>
  );
};
```

### 12.2 Create Route
Location: `apps/web/src/features/landing/routes/index.tsx`

```typescript
// apps/web/src/features/landing/routes/index.tsx
import { RouteObject } from 'react-router-dom';
import { LandingPage } from '../pages/LandingPage';

export const landingRoutes: RouteObject[] = [
  {
    path: '/',
    element: <LandingPage />,
  },
];
```

### 12.3 Update Main Router
Location: `apps/web/src/router.tsx`

- [ ] Import and add `landingRoutes`
- [ ] Ensure landing page is the default route

---

## Phase 13: Animations & Polish

### 13.1 Scroll Animations
- [ ] Wrap each section with animation wrapper:
  ```tsx
  <motion.div
    initial="hidden"
    whileInView="visible"
    viewport={{ once: true, margin: '-100px' }}
    variants={fadeInUp}
  >
    {children}
  </motion.div>
  ```
- [ ] Add stagger to grid items
- [ ] Add parallax effects (subtle)

### 13.2 Micro-interactions
- [ ] Button hover/press states (scale)
- [ ] Card hover lift effect
- [ ] Link underline animations
- [ ] Form input focus states

### 13.3 Performance
- [ ] Lazy load images below the fold
- [ ] Use `loading="lazy"` on `<img>` tags
- [ ] Optimize images (WebP format)
- [ ] Use `React.lazy()` for heavy sections

---

## Phase 14: Responsive Design


### 14.1 Breakpoint Adaptations
Using MUI breakpoints: `xs`, `sm`, `md`, `lg`, `xl`

- [ ] Mobile header → Hamburger + Drawer
- [ ] Hero → Stack content vertically, reduce font sizes
- [ ] Logo carousel → Single row, smaller logos
- [ ] Features → Stack cards vertically
- [ ] Benefits → 2 columns on tablet, 1 on mobile
- [ ] Testimonials → Single card visible, swipe on mobile
- [ ] Footer → Stack columns vertically

### 14.2 Mobile-Specific Styles
```tsx
sx={{
  display: { xs: 'none', md: 'flex' },     // Hide on mobile
  display: { xs: 'flex', md: 'none' },     // Show only on mobile
  fontSize: { xs: '2rem', md: '3.5rem' },  // Responsive font
  py: { xs: 4, md: 8 },                    // Responsive padding
}}
```

---

## Phase 15: SEO & Accessibility

### 15.1 SEO Setup
- [ ] Install `react-helmet-async`
- [ ] Add page meta in `LandingPage.tsx`:
  ```tsx
  <Helmet>
    <title>Stylipp - AI Personal Stylist | Discover Your Perfect Look</title>
    <meta name="description" content="Get personalized fashion recommendations powered by AI. Upload your style, swipe to train, and discover clothes you'll love." />
    <meta property="og:title" content="Stylipp - AI Personal Stylist" />
    <meta property="og:description" content="Discover your perfect look with AI-powered styling" />
    <meta property="og:image" content="/og-image.png" />
    <meta name="twitter:card" content="summary_large_image" />
  </Helmet>
  ```

### 15.2 Accessibility
- [ ] Add `aria-label` to icon buttons
- [ ] Ensure color contrast meets WCAG AA
- [ ] Test keyboard navigation
- [ ] Add skip-to-content link
- [ ] Ensure all images have `alt` text

---

## Data Files

### Static Data
Location: `apps/web/src/features/landing/`

- [ ] Create `data/testimonials.ts`
- [ ] Create `data/features.ts`
- [ ] Create `data/benefits.ts`
- [ ] Create `data/partners.ts` (logos)

---

## Dependencies

```bash
# Already in project per PROJECT_PLAN.md
@mui/material
@mui/icons-material
@emotion/react
@emotion/styled
framer-motion
react-router-dom

# Additional for landing page
npm install embla-carousel-react react-helmet-async
```

---

## Priority Order

| Priority | Phase | Description |
|----------|-------|-------------|
| ⚡ P0 | 1-2 | Feature setup + Shared components |
| ⚡ P0 | 3-4 | Header + Hero (above the fold) |
| ⚡ P0 | 5 | Logo Carousel (social proof) |
| 🔶 P1 | 6-7 | Features + How It Works |
| 🔶 P1 | 8-9 | Benefits + Testimonials |
| 🔶 P1 | 10-11 | CTA + Footer |
| 🔷 P2 | 12-13 | Assembly + Animations |
| 🔷 P2 | 14-15 | Responsive + SEO |

---

## Integration with Existing Features

The landing page CTAs should navigate to:
- **"Get Started Free"** → `/onboarding` (from `features/onboarding/`)
- **"Log In"** → `/auth/login` (from `features/auth/`)
- **"Watch Demo"** → Modal or external link

---

## Notes

- All content should support **Hebrew and English** (RTL support)
- Dark theme is the default and only theme for landing
- Prioritize Core Web Vitals performance
- Test on iOS Safari and Chrome for PWA compatibility
- Keep bundle size minimal - lazy load where possible

---

*Created: February 2026*