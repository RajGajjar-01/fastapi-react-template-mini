import { LoaderCircle } from 'lucide-react'
import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router'
import { toast } from 'sonner'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import {
  Field,
  FieldContent,
  FieldError,
  FieldLabel,
} from '@/components/ui/field'
import { useAuth } from '@/hooks/useAuth'
import { useAuthStore } from '@/stores/useAuthStore'
import { signupSchema, type SignupFormData } from '@/lib/schemas'

export default function SignupPage() {
  const navigate = useNavigate()
  const { user, loading } = useAuth()
  const [submitted, setSubmitted] = useState(false)
  const [submittedEmail, setSubmittedEmail] = useState('')
  const signup = useAuthStore((s) => s.signup)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      fullName: '',
      email: '',
      password: '',
      confirmPassword: '',
    },
  })

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  const onSubmit = async (data: SignupFormData) => {
    try {
      await signup(data.email, data.password, data.fullName)
      setSubmittedEmail(data.email)
      setSubmitted(true)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Signup failed')
    }
  }

  if (submitted) {
    return (
      <div className="min-h-dvh flex items-center justify-center overflow-hidden">
        <div className="w-full max-w-[420px] text-center p-6">
          <h1 className="mb-2 text-2xl font-semibold tracking-tight">Check your inbox</h1>
          <p className="mb-6 text-sm text-muted-foreground">
            We&apos;ve sent a verification link to <strong>{submittedEmail}</strong>. Please click
            the link to verify your email address before signing in.
          </p>
          <Button
            onClick={() => navigate('/login')}
            className="w-full"
          >
            Back to sign in
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-dvh flex items-center justify-center overflow-hidden">
      <div className="w-full max-w-[420px]">
        <Card className="relative z-[1] border ring-0  gap-0">
          <CardHeader className="p-6 border-b ">
            <p className="text-xs font-medium tracking-[0.1em] uppercase text-muted-foreground">
              Get started
            </p>
            <CardTitle className="text-2xl font-semibold tracking-tight">Create your account</CardTitle>
            <CardDescription className="text-sm">
              Create your account and get started
            </CardDescription>
          </CardHeader>

          <CardContent className="p-6 space-y-4">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <Field>
                <FieldLabel>Full name</FieldLabel>
                <FieldContent>
                  <Input
                    type="text"
                    placeholder="Your full name"
                    autoComplete="name"
                    disabled={loading || isSubmitting}
                    {...register('fullName')}
                  />
                  <FieldError errors={[errors.fullName]} />
                </FieldContent>
              </Field>

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
                <FieldLabel>Password</FieldLabel>
                <FieldContent>
                  <Input
                    type="password"
                    placeholder="Create a strong password"
                    autoComplete="new-password"
                    disabled={loading || isSubmitting}
                    {...register('password')}
                  />
                  <FieldError errors={[errors.password]} />
                </FieldContent>
              </Field>

              <Field>
                <FieldLabel>Confirm password</FieldLabel>
                <FieldContent>
                  <Input
                    type="password"
                    placeholder="Re-enter your password"
                    autoComplete="new-password"
                    disabled={loading || isSubmitting}
                    {...register('confirmPassword')}
                  />
                  <FieldError errors={[errors.confirmPassword]} />
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
                    Creating account...
                  </span>
                ) : (
                  'Get started'
                )}
              </Button>
            </form>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <Separator />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted-foreground">
                  Already have an account?
                </span>
              </div>
            </div>

            <a
              href="/login"
              onClick={(e) => { e.preventDefault(); navigate('/login') }}
              className="text-sm text-primary hover:underline text-center block w-full"
            >
              Sign in instead
            </a>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
