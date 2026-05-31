import { MailCheck } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useTheme } from '@/components/theme-provider'

export default function ForgotPasswordPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!email) {
      toast.error('Please enter your email address')
      return
    }
    setSubmitted(true)
  }

  if (submitted) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="mx-auto w-full max-w-sm px-6 text-center">
          <MailCheck className="mx-auto mb-4 h-12 w-12 text-emerald-500" />
          <h1 className="mb-2 text-2xl font-semibold tracking-tight">Email sent</h1>
          <p className="mb-6 text-sm text-muted-foreground">
            If an account exists for <strong>{email}</strong>, you will receive a password reset
            link shortly.
          </p>
          <Button onClick={() => navigate('/login')} className="w-full bg-[#F2771A] hover:bg-[#F2771A]/90 text-white border-transparent">
            Back to sign in
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
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
          <h1 className="text-2xl font-semibold tracking-tight">Reset your password</h1>
          <p className="text-sm text-muted-foreground">
            Enter your email address and we&apos;ll send you a link to reset your password.
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
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <Button type="submit" className="w-full bg-[#F2771A] hover:bg-[#F2771A]/90 text-white border-transparent">
            Send reset link
          </Button>

          <Button
            type="button"
            variant="ghost"
            className="w-full"
            onClick={() => navigate('/login')}
          >
            Back to sign in
          </Button>
        </form>
      </div>
    </div>
  )
}
