import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { LandingPage } from './features/landing/pages/LandingPage'
import LoginPage from './features/auth/components/LoginPage'
import RegisterPage from './features/auth/components/RegisterPage'
import PrivateRoute from './shared/components/PrivateRoute'
import OnboardingGate from './shared/components/OnboardingGate'
import OnboardingLayout from './features/onboarding/components/OnboardingLayout'
import PhotoUploadStep from './features/onboarding/components/PhotoUploadStep'
import CalibrationStep from './features/onboarding/components/CalibrationStep'
import ProfileStep from './features/onboarding/components/ProfileStep'
import OnboardingComplete from './features/onboarding/components/OnboardingComplete'
import FeedPage from './features/feed/pages/FeedPage'
import NotFoundPage from './pages/NotFoundPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Auth required, onboarding NOT required */}
        <Route element={<PrivateRoute />}>
          <Route path="/onboarding" element={<OnboardingLayout />}>
            <Route index element={<Navigate to="photos" replace />} />
            <Route path="photos" element={<PhotoUploadStep />} />
            <Route path="calibrate" element={<CalibrationStep />} />
            <Route path="profile" element={<ProfileStep />} />
            <Route path="complete" element={<OnboardingComplete />} />
          </Route>
        </Route>

        {/* Auth + onboarding required */}
        <Route element={<PrivateRoute />}>
          <Route element={<OnboardingGate />}>
            <Route path="/feed" element={<FeedPage />} />
          </Route>
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}
