import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { LandingPage } from './features/landing/pages/LandingPage'
import LoginPage from './features/auth/components/LoginPage'
import RegisterPage from './features/auth/components/RegisterPage'
import PrivateRoute from './shared/components/PrivateRoute'
import OnboardingLayout from './features/onboarding/components/OnboardingLayout'
import PhotoUploadStep from './features/onboarding/components/PhotoUploadStep'
import NotFoundPage from './pages/NotFoundPage'

function CalibrationStep() {
  return <div>Calibration coming soon (Plan 04-05)</div>
}

function ProfileStep() {
  return <div>Profile coming soon (Plan 04-05)</div>
}

function OnboardingComplete() {
  return <div>Onboarding complete! (Plan 04-05)</div>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected routes */}
        <Route element={<PrivateRoute />}>
          <Route path="/onboarding" element={<OnboardingLayout />}>
            <Route index element={<Navigate to="photos" replace />} />
            <Route path="photos" element={<PhotoUploadStep />} />
            <Route path="calibrate" element={<CalibrationStep />} />
            <Route path="profile" element={<ProfileStep />} />
            <Route path="complete" element={<OnboardingComplete />} />
          </Route>
          <Route path="/feed" element={<div>Feed (Phase 5)</div>} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}
