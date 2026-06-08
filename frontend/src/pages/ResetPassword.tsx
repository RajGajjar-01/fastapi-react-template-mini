import { Eye, EyeOff, KeyRound } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useTheme } from '@/components/theme-provider'
import { api } from '@/lib/api'

/**
 * ResetPasswordPage
 *
 * Shown when the user clicks the password-reset link from their email.
 * Expects a `token` query param:  /reset-password?token=<jwt>
 *
 * Wire up:
 *   1. Add <Route path="/reset-password" element={<ResetPasswordPage />} /> in App.tsx
 *   2. Your backend should accept POST /auth/reset-password  { token, password }
 */
export default function ResetPasswordPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const token = searchParams.get('token')

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading] = useState(false)

  // If there's no token in the URL, the link is invalid/expired
  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="mx-auto w-full max-w-sm px-6 text-center">
          <div className="mb-4 flex justify-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-destructive/10">
              <KeyRound className="h-7 w-7 text-destructive" />
            </div>
          </div>
          <h1 className="mb-2 text-2xl font-semibold tracking-tight">Invalid reset link</h1>
          <p className="mb-6 text-sm text-muted-foreground">
            This password reset link is invalid or has expired. Please request a new one.
          </p>
          <Button className="w-full" onClick={() => navigate('/forgot-password')}>
            Request new link
          </Button>
        </div>
      </div>
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (password.length < 8) {
      toast.error('Password must be at least 8 characters')
      return
    }
    if (password !== confirmPassword) {
      toast.error('Passwords do not match')
      return
    }

    setLoading(true)
    try {
      await api.post('/auth/reset-password', { token, password })
      toast.success('Password reset successfully', {
        description: 'You can now sign in with your new password.',
      })
      navigate('/login', { replace: true })
    } catch (err) {
      const data = (err as { response?: { data?: { error?: { detail?: string } } } })?.response?.data
      const message = data?.error?.detail ?? (err instanceof Error ? err.message : 'Failed to reset password. The link may have expired.')
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="mx-auto w-full max-w-sm px-6">
        {/* Logo */}
        <div className="mb-6 flex flex-col items-center justify-center">
          <picture>
            <source
              srcSet={isDark ? '/assets/logo-head-light.webp' : '/assets/logo-head.webp'}
              type="image/webp"
            />
            <img
              src={isDark ? '/assets/logo-head-light.png' : '/assets/logo-head-fallback.png'}
              alt="Logo"
              className="h-14 w-auto"
            />
          </picture>
        </div>

        <div className="mb-8 space-y-2 text-center">
          <h1 className="text-2xl font-semibold tracking-tight">Set new password</h1>
          <p className="text-sm text-muted-foreground">
            Choose a strong password for your account.
          </p>
        </div>



        <form onSubmit={handleSubmit} className="space-y-4">
          {/* New password */}
          <div className="space-y-2">
            <Label htmlFor="password">New password</Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Min. 8 characters"
                autoComplete="new-password"
                required
                disabled={loading}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pr-10"
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                onClick={() => setShowPassword((v) => !v)}
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {/* Confirm password */}
          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm new password</Label>
            <div className="relative">
              <Input
                id="confirmPassword"
                type={showConfirm ? 'text' : 'password'}
                placeholder="Repeat your password"
                autoComplete="new-password"
                required
                disabled={loading}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="pr-10"
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                onClick={() => setShowConfirm((v) => !v)}
                tabIndex={-1}
              >
                {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Saving...' : 'Reset password'}
          </Button>

          <Button
            type="button"
            variant="ghost"
            className="w-full"
            disabled={loading}
            onClick={() => navigate('/login')}
          >
            Back to sign in
          </Button>
        </form>
      </div>
    </div>
  )
}
