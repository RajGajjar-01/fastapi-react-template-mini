import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Button } from '@/components/ui/button'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

/**
 * Catches any unhandled error thrown during rendering in the child tree and
 * renders a friendly fallback instead of crashing the whole app to a blank screen.
 *
 * Usage: wrap your top-level routes (or any risky subtree) with <ErrorBoundary>.
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // In production you'd send this to a monitoring service like Sentry
    console.error('[ErrorBoundary] Uncaught error:', error, info.componentStack)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
    window.location.href = '/'
  }

  render() {
    if (!this.state.hasError) return this.props.children

    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background px-6 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-destructive/10">
          <span className="text-3xl">⚠️</span>
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">Something went wrong</h1>
          <p className="max-w-sm text-sm text-muted-foreground">
            An unexpected error occurred. Our team has been notified. You can try refreshing the
            page or returning to the home screen.
          </p>
        </div>

        {/* Show error message only in development */}
        {import.meta.env.DEV && this.state.error && (
          <pre className="max-w-lg overflow-auto rounded-lg border bg-muted p-4 text-left text-xs text-muted-foreground">
            {this.state.error.message}
          </pre>
        )}

        <div className="flex gap-3">
          <Button variant="outline" onClick={() => window.location.reload()}>
            Refresh page
          </Button>
          <Button onClick={this.handleReset}>Go to home</Button>
        </div>
      </div>
    )
  }
}
