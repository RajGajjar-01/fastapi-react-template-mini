import { ChevronsUpDown, Home, LogOut, Moon, Sun, User } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar'
import { useTheme } from '@/components/theme-provider'
import { useAuth } from '@/hooks/useAuth'

type Item = {
  icon: typeof Home
  title: string
  path: string
}

const baseItems: Item[] = [
  { icon: Home, title: 'Dashboard', path: '/dashboard' },
]

function getInitials(name: string | null | undefined): string {
  if (!name) return '?'
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export function AppSidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuth()
  const { isMobile, setOpenMobile, state } = useSidebar()
  const { theme, setTheme } = useTheme()
  const isDark = theme === 'dark'

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  const items = baseItems

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="group-data-[collapsible=icon]:flex group-data-[collapsible=icon]:items-center group-data-[collapsible=icon]:px-0">
        <div className="flex items-center gap-2 px-4 py-4 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:justify-center">
          <picture>
            <source
              srcSet={isDark ? '/assets/logo-head-light.webp' : '/assets/logo-head.webp'}
              type="image/webp"
            />
            <img
              src={isDark ? '/assets/logo-head-light.png' : '/assets/logo-head-fallback.png'}
              alt="Logo"
              className="h-11 w-auto group-data-[collapsible=icon]:h-8"
            />
          </picture>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => {
                const isActive = location.pathname === item.path
                const handleClick = () => {
                  navigate(item.path)
                  if (isMobile) setOpenMobile(false)
                }
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      tooltip={state === 'collapsed' ? item.title : undefined}
                      isActive={isActive}
                      onClick={handleClick}
                    >
                      <item.icon />
                      <span>{item.title}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger
                render={
                  <SidebarMenuButton
                    className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                    tooltip={state === 'collapsed' ? user?.full_name || user?.email : undefined}
                  />
                }
              >
                <Avatar className="size-8">
                  <AvatarFallback className="bg-zinc-600 text-white text-xs">
                    {getInitials(user?.full_name)}
                  </AvatarFallback>
                </Avatar>
                <div className="grid flex-1 text-left text-sm leading-tight group-data-[collapsible=icon]:hidden">
                  <span className="truncate font-medium">{user?.full_name || 'User'}</span>
                  <span className="truncate text-xs text-muted-foreground">{user?.email}</span>
                </div>
                <ChevronsUpDown className="ml-auto size-4 text-muted-foreground group-data-[collapsible=icon]:hidden" />
              </DropdownMenuTrigger>
              <DropdownMenuContent
                className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
                side={isMobile ? 'bottom' : 'right'}
                align="end"
                sideOffset={4}
              >
                <div className="px-1.5 py-1 text-xs text-muted-foreground p-0 font-normal">
                  <div className="flex items-center gap-2.5 px-1 py-1.5">
                    <Avatar className="size-8">
                      <AvatarFallback className="bg-zinc-600 text-white text-xs">
                        {getInitials(user?.full_name)}
                      </AvatarFallback>
                    </Avatar>
                    <div className="grid flex-1 text-left text-sm leading-tight">
                      <span className="truncate font-medium text-foreground">{user?.full_name || 'User'}</span>
                      <span className="truncate text-xs text-muted-foreground">{user?.email}</span>
                    </div>
                  </div>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate('/profile')}>
                  <User />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
                  {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                  <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut />
                  Log Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  )
}
