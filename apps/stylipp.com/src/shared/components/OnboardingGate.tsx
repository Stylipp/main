import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/features/auth/stores/authStore'

export default function OnboardingGate() {
  const user = useAuthStore((state) => state.user)

  // If no user, render nothing — PrivateRoute handles auth redirect
  if (!user) {
    return null
  }

  // If user hasn't completed onboarding, redirect to onboarding flow
  if (!user.onboarding_completed) {
    return <Navigate to="/onboarding" replace />
  }

  // User is authenticated and has completed onboarding — render children
  return <Outlet />
}
