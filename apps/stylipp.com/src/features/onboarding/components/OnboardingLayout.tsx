import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Box from '@mui/material/Box'
import MobileStepper from '@mui/material/MobileStepper'
import { AnimatePresence, motion } from 'framer-motion'

const STEPS = [
  { path: 'photos', label: 'Upload Photos' },
  { path: 'calibrate', label: 'Style Calibration' },
  { path: 'profile', label: 'Your Profile' },
]

const slideVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? '100%' : '-100%',
    opacity: 0,
  }),
  center: {
    x: 0,
    opacity: 1,
  },
  exit: (direction: number) => ({
    x: direction < 0 ? '100%' : '-100%',
    opacity: 0,
  }),
}

function getStepIndex(pathname: string): number {
  const idx = STEPS.findIndex((s) => pathname.includes(s.path))
  return idx >= 0 ? idx : 0
}

export default function OnboardingLayout() {
  const location = useLocation()
  const currentStep = getStepIndex(location.pathname)

  // Track previous step to compute slide direction.
  // Uses the "adjusting state during render" pattern:
  // https://react.dev/learn/you-might-not-need-an-effect#adjusting-some-state-when-a-prop-changes
  const [prevStep, setPrevStep] = useState(currentStep)
  const [direction, setDirection] = useState(1)

  if (currentStep !== prevStep) {
    setDirection(currentStep > prevStep ? 1 : -1)
    setPrevStep(currentStep)
  }

  return (
    <Box
      sx={{
        minHeight: '100dvh',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.default',
      }}
    >
      {/* Step content with slide animation */}
      <Box sx={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={location.pathname}
            custom={direction}
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ type: 'tween', ease: 'easeInOut', duration: 0.3 }}
            style={{ height: '100%' }}
          >
            <Box sx={{ height: '100%', p: 2 }}>
              <Outlet />
            </Box>
          </motion.div>
        </AnimatePresence>
      </Box>

      {/* Bottom stepper — dots only, no Next/Back buttons */}
      <MobileStepper
        variant="dots"
        steps={STEPS.length}
        position="static"
        activeStep={Math.max(0, currentStep)}
        nextButton={<Box />}
        backButton={<Box />}
        sx={{
          bgcolor: 'background.default',
          justifyContent: 'center',
          pb: 2,
          '& .MuiMobileStepper-dots': {
            gap: 1,
          },
        }}
      />
    </Box>
  )
}
