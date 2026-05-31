import { useEffect } from 'react'
import { Navigate, Route, Routes } from 'react-router'
import { Toaster } from '@/components/ui/sonner'
import DashboardLayout from '@/components/DashboardLayout'
import ErrorBoundary from '@/components/ErrorBoundary'
// Components
import ProtectedRoute from '@/components/ProtectedRoute'
import { ThemeProvider } from '@/components/theme-provider'
import DashboardPage from '@/pages/Dashboard'
import ForgotPasswordPage from '@/pages/ForgotPassword'
// Pages
import LoginPage from '@/pages/Login'
import NotFoundPage from '@/pages/NotFound'
import ProfilePage from '@/pages/Profile'
import ResetPasswordPage from '@/pages/ResetPassword'
import SignupPage from '@/pages/Signup'
import VerifyEmailPage from '@/pages/VerifyEmail'
import { useAuthStore } from '@/stores/useAuthStore'

export default function App() {
  const initialize = useAuthStore((s) => s.initialize)

  // Check auth status once on app mount
  useEffect(() => {
    initialize()
  }, [initialize])

  return (
    <ThemeProvider defaultTheme="dark" storageKey="app-theme">
      {/* Global toast renderer — place once, use toast() anywhere in the app */}
      <Toaster richColors closeButton position="top-right" />

      {/* Catches any unhandled render error and shows a recovery screen */}
      <ErrorBoundary>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/verify-email" element={<VerifyEmailPage />} />

          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/profile" element={<ProfilePage />} />
            </Route>
          </Route>

          {/* 404 — replaces the silent catch-all redirect */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </ErrorBoundary>
    </ThemeProvider>
  )
}
