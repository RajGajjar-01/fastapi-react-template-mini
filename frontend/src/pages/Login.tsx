import { useEffect } from 'react'
import { LoaderCircle } from 'lucide-react'
import { Navigate, useNavigate } from 'react-router'
import { toast } from 'sonner'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import {
  Field,
  FieldContent,
  FieldError,
  FieldLabel,
} from '@/components/ui/field'
import { useAuth } from '@/hooks/useAuth'
import { loginSchema, type LoginFormData } from '@/lib/schemas'

export default function LoginPage() {
  const navigate = useNavigate()
  const { user, login, loading, error } = useAuth()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  })

  useEffect(() => {
    if (error) {
      toast.error(error)
    }
  }, [error])

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data.email, data.password)
      navigate('/dashboard', { replace: true })
    } catch {
      // error is already stored in `error` state by useAuthStore
    }
  }

  return (
    <div className="min-h-dvh flex items-center justify-center overflow-hidden">
      <div className="w-full max-w-[420px]">
        <main className="relative z-[1] bg-card border rounded-xl">
          <div className="p-6 border-b">
            <p className="text-xs font-medium tracking-[0.1em] uppercase text-muted-foreground">
              Welcome back
            </p>
            <h1 className="text-2xl font-semibold tracking-tight mt-1">Sign in</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Enter your credentials to access your dashboard
            </p>
          </div>

          <div className="p-6 space-y-4">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <Field>
                <FieldLabel>Email address</FieldLabel>
                <FieldContent>
                  <Input
                    type="email"
                    placeholder="you@example.com"
                    autoComplete="email"
                    disabled={loading || isSubmitting}
                    {...register('email')}
                  />
                  <FieldError errors={[errors.email]} />
                </FieldContent>
              </Field>

              <Field>
                <div className="flex items-center justify-between">
                  <FieldLabel>Password</FieldLabel>
                  <a
                    href="/forgot-password"
                    className="text-xs text-primary hover:underline"
                  >
                    Forgot password?
                  </a>
                </div>
                <FieldContent>
                  <Input
                    type="password"
                    placeholder="Enter your password"
                    autoComplete="current-password"
                    disabled={loading || isSubmitting}
                    {...register('password')}
                  />
                  <FieldError errors={[errors.password]} />
                </FieldContent>
              </Field>

              <Button
                type="submit"
                className="w-full"
                disabled={loading || isSubmitting}
              >
                {loading || isSubmitting ? (
                  <span className="flex items-center gap-2">
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                    Signing in...
                  </span>
                ) : (
                  'Sign in'
                )}
              </Button>
            </form>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <Separator />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted-foreground">New here?</span>
              </div>
            </div>

            <a
              href="/signup"
              onClick={(e) => { e.preventDefault(); navigate('/signup') }}
              className="text-sm text-primary hover:underline text-center block w-full"
            >
              Create an account
            </a>
          </div>
        </main>
      </div>
    </div>
  )
}
