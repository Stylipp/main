import { useCallback, useEffect, useState } from 'react'
import { Box, Chip, IconButton, Typography } from '@mui/material'
import { ChevronLeft, ChevronRight } from '@mui/icons-material'
import { motion } from 'framer-motion'
import useEmblaCarousel from 'embla-carousel-react'
import { SectionContainer } from '@/shared/components'
import { TestimonialCard } from './TestimonialCard'
import { fadeInUp, staggerContainer } from '../../utils/animations'
import type { Testimonial } from '../../types/landing.types'

const testimonials: Testimonial[] = [
  {
    id: '1',
    companyLogo: '',
    companyName: 'Fashion Forward',
    quote: 'Stylipp transformed how I shop for clothes!',
    fullText:
      "I used to spend hours scrolling through online stores. Now, Stylipp shows me exactly what I'll love. It's like having a personal stylist in my pocket.",
    authorName: 'Sarah M.',
    authorRole: 'Fashion Enthusiast',
  },
  {
    id: '2',
    companyLogo: '',
    companyName: 'Style Studio',
    quote: 'The AI recommendations are incredibly accurate.',
    fullText:
      'After just a few swipes, Stylipp understood my style better than I do! Every recommendation feels handpicked for me.',
    authorName: 'David L.',
    authorRole: 'Creative Director',
  },
  {
    id: '3',
    companyLogo: '',
    companyName: 'Trend Setters',
    quote: 'Finally, an app that gets my aesthetic.',
    fullText:
      "I've tried many styling apps, but Stylipp is different. It actually learns and improves. My wardrobe has never looked better.",
    authorName: 'Maya R.',
    authorRole: 'Content Creator',
  },
  {
    id: '4',
    companyLogo: '',
    companyName: 'Urban Chic',
    quote: 'Saved me so much time and money.',
    fullText:
      'No more impulse buys that sit in my closet. Stylipp helps me build a cohesive wardrobe with pieces I actually wear.',
    authorName: 'Alex K.',
    authorRole: 'Business Professional',
  },
]

export const TestimonialsSection = () => {
  const [emblaRef, emblaApi] = useEmblaCarousel({
    loop: true,
    align: 'start',
    slidesToScroll: 1,
  })

  const [canScrollPrev, setCanScrollPrev] = useState(false)
  const [canScrollNext, setCanScrollNext] = useState(true)

  const scrollPrev = useCallback(() => emblaApi?.scrollPrev(), [emblaApi])
  const scrollNext = useCallback(() => emblaApi?.scrollNext(), [emblaApi])

  const onSelect = useCallback(() => {
    if (!emblaApi) return
    setCanScrollPrev(emblaApi.canScrollPrev())
    setCanScrollNext(emblaApi.canScrollNext())
  }, [emblaApi])

  useEffect(() => {
    if (!emblaApi) return
    emblaApi.on('select', onSelect)
    emblaApi.on('reInit', onSelect)
    // Defer initial state update to avoid synchronous setState in effect
    queueMicrotask(onSelect)
    return () => {
      emblaApi.off('select', onSelect)
      emblaApi.off('reInit', onSelect)
    }
  }, [emblaApi, onSelect])

  return (
    <Box
      component="section"
      sx={{
        bgcolor: '#f8f9fc',
      }}
    >
      <SectionContainer maxWidth="lg">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          variants={staggerContainer}
        >
          <Box sx={{ textAlign: 'center', mb: 6 }}>
            <motion.div variants={fadeInUp}>
              <Chip
                label="Testimonials"
                sx={{
                  mb: 2,
                  bgcolor: 'rgba(91,74,228,0.1)',
                  color: 'primary.main',
                  fontWeight: 500,
                }}
              />
            </motion.div>
            <motion.div variants={fadeInUp}>
              <Typography variant="h2" sx={{ mb: 2 }}>
                Why users love Stylipp
              </Typography>
            </motion.div>
            <motion.div variants={fadeInUp}>
              <Typography
                variant="body1"
                sx={{ color: 'text.secondary', maxWidth: 500, mx: 'auto' }}
              >
                Join thousands of satisfied users who have transformed their style journey.
              </Typography>
            </motion.div>
          </Box>

          <motion.div variants={fadeInUp}>
            <Box sx={{ position: 'relative' }}>
              <Box ref={emblaRef} sx={{ overflow: 'hidden' }}>
                <Box sx={{ display: 'flex', gap: 3 }}>
                  {testimonials.map((testimonial) => (
                    <Box
                      key={testimonial.id}
                      sx={{
                        flex: '0 0 100%',
                        minWidth: 0,
                        '@media (min-width: 600px)': {
                          flex: '0 0 50%',
                        },
                        '@media (min-width: 900px)': {
                          flex: '0 0 33.333%',
                        },
                      }}
                    >
                      <TestimonialCard testimonial={testimonial} />
                    </Box>
                  ))}
                </Box>
              </Box>

              {/* Navigation */}
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  gap: 2,
                  mt: 4,
                }}
              >
                <IconButton
                  onClick={scrollPrev}
                  disabled={!canScrollPrev}
                  sx={{
                    border: '1px solid rgba(0,0,0,0.15)',
                    '&:hover': {
                      bgcolor: 'rgba(0,0,0,0.04)',
                    },
                    '&.Mui-disabled': {
                      opacity: 0.3,
                    },
                  }}
                  aria-label="Previous testimonial"
                >
                  <ChevronLeft />
                </IconButton>
                <IconButton
                  onClick={scrollNext}
                  disabled={!canScrollNext}
                  sx={{
                    border: '1px solid rgba(0,0,0,0.15)',
                    '&:hover': {
                      bgcolor: 'rgba(0,0,0,0.04)',
                    },
                    '&.Mui-disabled': {
                      opacity: 0.3,
                    },
                  }}
                  aria-label="Next testimonial"
                >
                  <ChevronRight />
                </IconButton>
              </Box>
            </Box>
          </motion.div>
        </motion.div>
      </SectionContainer>
    </Box>
  )
}
