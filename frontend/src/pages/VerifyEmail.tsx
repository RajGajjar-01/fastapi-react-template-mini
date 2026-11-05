import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

export default function VerifyEmailPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('Checking your link...')

  useEffect(() => {
    const token = searchParams.get('token')
    const type = searchParams.get('type')
    const errorDescription = searchParams.get('error_description')

    const timer = setTimeout(() => {
      if (errorDescription) {
        setStatus('error')
        setMessage(errorDescription.replace(/\+/g, ' ').slice(0, 200))
      } else if (token && type === 'signup') {
        // The auth service confirms the address before it sends the user here.
        // This page cannot check that, so it does not claim to.
        setStatus('success')
        setMessage('If your email was confirmed, you can sign in now.')
      } else {
        setStatus('error')
        setMessage('The verification link is invalid or has expired.')
      }
    }, 2000)

    return () => clearTimeout(timer)
  }, [searchParams])

  return (
    <div className="flex min-h-screen">
      <div className="flex w-full items-center justify-center bg-background">
        <div className="mx-auto w-full max-w-sm px-6 text-center">
          <Card>
            <CardContent className="pt-6">
              {status === 'loading' && (
                <div className="flex flex-col items-center gap-4 py-8">
                  <div className="h-10 w-10 animate-spin rounded-full border-4 border-muted-foreground/20 border-t-success" />
                  <p className="text-sm text-muted-foreground">{message}</p>
                </div>
              )}

              {status === 'success' && (
                <div className="flex flex-col items-center gap-4 py-8">
                  <h2 className="text-xl font-semibold">Email link opened</h2>
                  <p className="text-sm text-muted-foreground">{message}</p>
                  <Button onClick={() => navigate('/login')} className="mt-2 w-full">
                    Continue to sign in
                  </Button>
                </div>
              )}

              {status === 'error' && (
                <div className="flex flex-col items-center gap-4 py-8">
                  <h2 className="text-xl font-semibold">Verification failed</h2>
                  <p className="text-sm text-muted-foreground">{message}</p>
                  <Button onClick={() => navigate('/login')} className="mt-2 w-full">
                    Back to sign in
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
