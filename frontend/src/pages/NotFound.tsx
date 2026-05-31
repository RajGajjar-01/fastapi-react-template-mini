import { useNavigate } from 'react-router'
import { Button } from '@/components/ui/button'

/**
 * 404 Not Found page.
 * Shown for any route that doesn't match the router config.
 * Replace <Route path="*" element={<Navigate to="/" />} /> with this in App.tsx.
 */
export default function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background px-6 text-center">
      <div className="space-y-1">
        <p className="text-8xl font-bold tracking-tighter text-muted-foreground/30">404</p>
        <h1 className="text-2xl font-semibold tracking-tight">Page not found</h1>
        <p className="max-w-sm text-sm text-muted-foreground">
          The page you're looking for doesn't exist or has been moved.
        </p>
      </div>

      <div className="flex gap-3">
        <Button variant="outline" onClick={() => navigate(-1)}>
          Go back
        </Button>
        <Button onClick={() => navigate('/', { replace: true })}>Home</Button>
      </div>
    </div>
  )
}
