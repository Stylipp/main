import type { RouteObject } from 'react-router-dom'
import { LandingPage } from '../pages/LandingPage'

export const landingRoutes: RouteObject[] = [
  {
    path: '/',
    element: <LandingPage />,
  },
]
