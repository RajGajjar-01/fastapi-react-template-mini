import { Heart, Sparkles } from 'lucide-react'
import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { useAuth } from '@/hooks/useAuth'
import { useAuthStore } from '@/stores/useAuthStore'
import { useTheme } from '@/components/theme-provider'

export default function SignupPage() {
  const navigate = useNavigate()
  const { user, loading } = useAuth()
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const signup = useAuthStore((s) => s.signup)

  // While the /auth/me check is in-flight, render nothing
  if (loading) return null

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (password !== confirmPassword) {
      toast.error('Passwords do not match')
      return
    }

    if (password.length < 6) {
      toast.error('Password must be at least 6 characters')
      return
    }

    try {
      await signup(email, password, fullName)
      setSubmitted(true)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Signup failed')
    }
  }

  if (submitted) {
    return (
      <div className="flex min-h-screen">
        <div className="relative hidden w-1/2 lg:block" style={{ backgroundColor: '#00255B' }}>
        <video
          autoPlay
          loop
          muted
          playsInline
          className="absolute inset-0 h-full w-full object-cover"
        >
          <source src="/videos/rocket-launch.mp4" type="video/mp4" />
        </video>
        <div
          className="absolute inset-0"
          style={{
            background:
              'linear-gradient(135deg, rgba(0,37,91,0.7) 0%, rgba(6,89,169,0.4) 50%, rgba(0,37,91,0.85) 100%)',
          }}
        />
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

      <div className="flex w-full flex-col justify-center bg-background lg:w-1/2">
        <div className="mx-auto w-full max-w-sm px-6 text-center">
          <Sparkles className="mx-auto mb-4 h-12 w-12" style={{ color: '#F2771A' }} />
            <h1 className="mb-2 text-2xl font-semibold tracking-tight">Check your inbox</h1>
            <p className="mb-6 text-sm text-muted-foreground">
              We&apos;ve sent a verification link to <strong>{email}</strong>. Please click the link
              to verify your email address before signing in.
            </p>
            <Button
              onClick={() => navigate('/login')}
              className="w-full bg-[#F2771A] hover:bg-[#F2771A]/90 text-white border-transparent"
            >
              Back to sign in
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen">
      {/* Left side — Video / Brand */}
      <div className="relative hidden w-1/2 lg:block" style={{ backgroundColor: '#00255B' }}>
        <video
          autoPlay
          loop
          muted
          playsInline
          className="absolute inset-0 h-full w-full object-cover"
        >
          <source src="/videos/rocket-launch.mp4" type="video/mp4" />
        </video>
        <div
          className="absolute inset-0"
          style={{
            background:
              'linear-gradient(135deg, rgba(0,37,91,0.7) 0%, rgba(6,89,169,0.4) 50%, rgba(0,37,91,0.85) 100%)',
          }}
        />
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

      {/* Right side — Signup Form */}
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
            <h1 className="text-2xl font-semibold tracking-tight">Create your account</h1>
            <p className="text-sm text-muted-foreground">
              Create your account and take control of your health journey
            </p>
          </div>



          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="fullName">Full name</Label>
              <Input
                id="fullName"
                type="text"
                placeholder="Dr. Sarah Chen"
                autoComplete="name"
                required
                disabled={loading}
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>

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
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Create a strong password"
                autoComplete="new-password"
                required
                disabled={loading}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">Must be at least 6 characters</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm password</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="Re-enter your password"
                autoComplete="new-password"
                required
                disabled={loading}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>

            <Button
              type="submit"
              className="w-full bg-[#F2771A] hover:bg-[#F2771A]/90 text-white border-transparent"
              disabled={loading}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <Heart className="h-4 w-4 animate-pulse" />
                  Creating account...
                </span>
              ) : (
                'Get started'
              )}
            </Button>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <Separator />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">
                  Already have an account?
                </span>
              </div>
            </div>

            <Button
              variant="outline"
              className="mt-4 w-full"
              onClick={() => navigate('/login')}
              disabled={loading}
            >
              Sign in instead
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
