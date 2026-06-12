import { Heart } from 'lucide-react'
import { useState, useEffect } from 'react'
import { Navigate, useNavigate } from 'react-router'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { useAuth } from '@/hooks/useAuth'
import { useTheme } from '@/components/theme-provider'

export default function LoginPage() {
  const navigate = useNavigate()
  const { user, login, loading, error } = useAuth()
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  useEffect(() => {
    if (error) {
      toast.error(error)
    }
  }, [error])

  // While the /auth/me check is in-flight, render nothing so this page
  // never flashes on screen for an already-authenticated user.
  if (loading) return null

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await login(email, password)
      navigate('/dashboard', { replace: true })
    } catch {
      // error is already stored in `error` state by useAuthStore
    }
  }

  return (
    <div className="flex min-h-screen">
      {/* Left side — Brand */}
      <div className="relative hidden w-1/2 lg:block auth-gradient">
        <div className="absolute inset-0 flex flex-col justify-end p-12 text-white">
          <div className="space-y-4">
            <blockquote className="text-2xl font-light leading-relaxed">
              "The greatest wealth is health."
            </blockquote>
            <p className="text-sm text-white/80">
              — Virgil, Roman Poet
            </p>
          </div>
        </div>
      </div>

      {/* Right side — Login Form */}
      <div className="flex w-full flex-col justify-center bg-background lg:w-1/2">
        <div className="mx-auto w-full max-w-sm px-6">
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
            <h1 className="text-2xl font-semibold tracking-tight">Welcome back</h1>
            <p className="text-sm text-muted-foreground">
              Enter your credentials to access your dashboard
            </p>
          </div>



          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email address</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                autoComplete="email"
                required
                disabled={loading}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <a
                  href="/forgot-password"
                  className="text-xs text-primary hover:underline"
                >
                  Forgot password?
                </a>
              </div>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                autoComplete="current-password"
                required
                disabled={loading}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={loading}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <Heart className="h-4 w-4 animate-pulse" />
                  Signing in...
                </span>
              ) : (
                'Sign in'
              )}
            </Button>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <Separator />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">New here?</span>
              </div>
            </div>

            <Button
              variant="outline"
              className="mt-4 w-full"
              onClick={() => navigate('/signup')}
              disabled={loading}
            >
              Create an account
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
