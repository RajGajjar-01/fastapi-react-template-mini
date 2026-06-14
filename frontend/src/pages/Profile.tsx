import { Save } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/hooks/useAuth'

export default function ProfilePage() {
  const navigate = useNavigate()
  const { user, updateProfile } = useAuth()

  const [fullName, setFullName] = useState(user?.full_name ?? '')
  const [saving, setSaving] = useState(false)

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      await updateProfile(fullName || null, null)
      toast.success('Profile updated successfully')
    } catch {
      toast.error('Failed to update profile')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-xl min-h-dvh">
      <div className="mb-8 space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Your Profile</h1>
        <p className="text-sm text-muted-foreground">
          Manage your personal information and preferences
        </p>
      </div>

      <Card className="mb-6 ring-0 border">
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div>
              <h2 className="text-lg font-semibold">{user?.full_name || 'Your Profile'}</h2>
              <p className="text-sm text-muted-foreground">{user?.email}</p>
              <div className="mt-2 inline-flex items-center rounded-full bg-green-500/10 px-2.5 py-0.5 text-xs font-medium text-green-600">
                Active Member
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <form onSubmit={handleSave} className="space-y-6">
        <Card className="ring-0 border">
          <CardHeader className="border-b border-[var(--border)]">
            <CardTitle className="text-base">Profile Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={user?.email ?? ''} disabled />
              <p className="text-xs text-muted-foreground">Email cannot be changed</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="fullName">Full name</Label>
              <Input
                id="fullName"
                type="text"
                placeholder="Alex Rivera"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
          </CardContent>
          <CardFooter className="border-t border-[var(--border)] flex justify-end gap-3 bg-transparent">
            <Button type="button" variant="outline" onClick={() => navigate('/dashboard')}>
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? (
                <span className="flex items-center gap-2">
                  <Save className="h-4 w-4 animate-pulse" />
                  Saving...
                </span>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Save changes
                </>
              )}
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  )
}
