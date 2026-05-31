import { Navigate, Outlet } from 'react-router'
import { useAuth } from '@/hooks/useAuth'

export default function ProtectedRoute() {
  const { user, loading } = useAuth()

  // Stay invisible while /auth/me is resolving — no spinner, no flash
  if (loading) return null

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
