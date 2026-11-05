import { Shield } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/lib/api'

type Role = 'user' | 'moderator' | 'admin'

interface AdminUser {
  user_id: string
  email: string
  full_name: string | null
  role: Role
  created_at: string
}

const PAGE_SIZE = 50
const SKELETON_ROWS = ['row-1', 'row-2', 'row-3', 'row-4']

function roleBadgeVariant(role: Role): 'default' | 'secondary' | 'outline' {
  if (role === 'admin') return 'default'
  if (role === 'moderator') return 'secondary'
  return 'outline'
}

function getInitials(name: string | null, email: string): string {
  if (name) {
    return (
      name
        .split(' ')
        .filter(Boolean)
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2) || email[0].toUpperCase()
    )
  }
  return email[0].toUpperCase()
}

export default function AdminPage() {
  const { user } = useAuth()
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  const [loadingMore, setLoadingMore] = useState(false)

  const loadPage = useCallback(async (offset: number) => {
    const res = await api.get<{ data: AdminUser[]; meta: { total: number } }>('/admin/users', {
      params: { limit: PAGE_SIZE, offset },
    })
    setUsers((prev) => (offset === 0 ? res.data.data : [...prev, ...res.data.data]))
    setTotal(res.data.meta.total)
  }, [])

  useEffect(() => {
    loadPage(0)
      .catch(() => toast.error('Failed to load users'))
      .finally(() => setLoading(false))
  }, [loadPage])

  const handleLoadMore = async () => {
    setLoadingMore(true)
    try {
      await loadPage(users.length)
    } catch {
      toast.error('Failed to load more users')
    } finally {
      setLoadingMore(false)
    }
  }

  const handleRoleChange = async (userId: string, newRole: Role) => {
    const prev = users.find((u) => u.user_id === userId)?.role
    setUsers((us) => us.map((u) => (u.user_id === userId ? { ...u, role: newRole } : u)))
    setUpdating(userId)
    try {
      await api.patch(`/admin/users/${userId}/role`, { role: newRole })
      toast.success('Role updated')
    } catch {
      setUsers((us) => us.map((u) => (u.user_id === userId ? { ...u, role: prev! } : u)))
      toast.error('Failed to update role')
    } finally {
      setUpdating(null)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6 flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
          <Shield className="h-5 w-5 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Admin</h1>
          <p className="text-sm text-muted-foreground">Manage users and their roles</p>
        </div>
      </div>

      <Card className="border ring-0">
        <CardHeader className="border-b border-[var(--border)] py-4">
          <CardTitle className="text-base">
            Users
            {!loading && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                ({users.length} of {total})
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="divide-y divide-border">
              {SKELETON_ROWS.map((rowKey) => (
                <div key={rowKey} className="flex items-center gap-4 px-6 py-4">
                  <Skeleton className="h-9 w-9 rounded-full" />
                  <div className="flex-1 space-y-1.5">
                    <Skeleton className="h-4 w-36" />
                    <Skeleton className="h-3 w-52" />
                  </div>
                  <Skeleton className="h-6 w-20 rounded-full" />
                  <Skeleton className="h-8 w-28 rounded-md" />
                </div>
              ))}
            </div>
          ) : (
            <div className="divide-y divide-border">
              {users.map((u) => {
                const isSelf = u.user_id === user?.user_id
                return (
                  <div key={u.user_id} className="flex items-center gap-4 px-6 py-4">
                    {/* Avatar */}
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-zinc-600 text-xs font-medium text-white">
                      {getInitials(u.full_name, u.email)}
                    </div>

                    {/* Name + email */}
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">
                        {u.full_name || '—'}
                        {isSelf && (
                          <span className="ml-2 text-xs text-muted-foreground">(you)</span>
                        )}
                      </p>
                      <p className="truncate text-xs text-muted-foreground">{u.email}</p>
                    </div>

                    {/* Role badge */}
                    <Badge variant={roleBadgeVariant(u.role)} className="capitalize shrink-0">
                      {u.role}
                    </Badge>

                    {/* Joined date */}
                    <span className="shrink-0 text-xs text-muted-foreground w-24 text-right">
                      {new Date(u.created_at).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </span>

                    {/* Role select — only admins can assign roles */}
                    {user?.role === 'admin' && (
                      <select
                        value={u.role}
                        disabled={isSelf || updating === u.user_id}
                        onChange={(e) => handleRoleChange(u.user_id, e.target.value as Role)}
                        className="shrink-0 rounded-md border border-input bg-background px-2.5 py-1.5 text-xs text-foreground shadow-sm disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-ring"
                      >
                        <option value="user">User</option>
                        <option value="moderator">Moderator</option>
                        <option value="admin">Admin</option>
                      </select>
                    )}
                  </div>
                )
              })}

              {users.length === 0 && (
                <p className="px-6 py-8 text-center text-sm text-muted-foreground">
                  No users found
                </p>
              )}

              {users.length < total && (
                <div className="flex justify-center px-6 py-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleLoadMore}
                    disabled={loadingMore}
                  >
                    {loadingMore ? 'Loading...' : 'Load more'}
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
