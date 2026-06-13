import { Calendar, Heart, TrendingUp, User } from 'lucide-react'
import { useNavigate } from 'react-router'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/hooks/useAuth'

export default function DashboardPage() {
  const navigate = useNavigate()
  const { user } = useAuth()

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Welcome back
            {user ? (user.full_name ? `, ${user.full_name}` : ', ' + user.email.split('@')[0]) : ''}
          </h1>
          <p className="text-sm text-muted-foreground">
            Here&apos;s what&apos;s happening with your health journey
          </p>
        </div>
      </div>

      {/* Stats cards */}
      <div className="mb-8 grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Health Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">92</div>
            <p className="text-xs text-muted-foreground">+4 from last week</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Completed Sessions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">12</div>
            <p className="text-xs text-muted-foreground">This month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Upcoming</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">3</div>
            <p className="text-xs text-muted-foreground">Appointments</p>
          </CardContent>
        </Card>
      </div>

      {/* Recent activity */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            {
              icon: Heart,
              label: 'Completed mindfulness session',
              time: '2 hours ago',
              color: 'text-destructive',
            },
            {
              icon: Calendar,
              label: 'Scheduled nutrition consultation',
              time: 'Yesterday',
              color: 'text-primary',
            },
            {
              icon: TrendingUp,
              label: 'Weekly progress report generated',
              time: '3 days ago',
              color: 'text-green-600',
            },
          ].map((item, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
                <item.icon className={`h-4 w-4 ${item.color}`} />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">{item.label}</p>
                <p className="text-xs text-muted-foreground">{item.time}</p>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Quick action */}
      <div className="flex gap-3">
        <Button
          className="bg-green-600 hover:bg-green-700 text-white"
          onClick={() => navigate('/profile')}
        >
          <User className="mr-2 h-4 w-4" />
          Update Profile
        </Button>
        <Button variant="outline">
          <Calendar className="mr-2 h-4 w-4" />
          Book Appointment
        </Button>
      </div>
    </div>
  )
}
