import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { LandingPage } from './features/landing/pages/LandingPage'
import LoginPage from './features/auth/components/LoginPage'
import RegisterPage from './features/auth/components/RegisterPage'
import PrivateRoute from './shared/components/PrivateRoute'
import NotFoundPage from './pages/NotFoundPage'

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
          <Route path="/onboarding/*" element={<div>Onboarding (Plan 04-04)</div>} />
          <Route path="/feed" element={<div>Feed (Phase 5)</div>} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}
