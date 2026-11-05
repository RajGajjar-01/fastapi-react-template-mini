import { useAuth } from '@/hooks/useAuth'

export default function DashboardPage() {
  const { user } = useAuth()

  return (
    <div>
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Welcome back
          {user ? (user.full_name ? `, ${user.full_name}` : `, ${user.email.split('@')[0]}`) : ''}
        </h1>
        <p className="text-sm text-muted-foreground">Here&apos;s what&apos;s happening</p>
      </div>
    </div>
  )
}
