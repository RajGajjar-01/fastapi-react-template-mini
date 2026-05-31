import { PanelLeft } from 'lucide-react'
import { Outlet } from 'react-router'
import { AppSidebar } from '@/components/AppSidebar'
import { Button } from '@/components/ui/button'
import { SidebarProvider, useSidebar } from '@/components/ui/sidebar'
import { useTheme } from '@/components/theme-provider'

function MobileHeader() {
  const { openMobile, setOpenMobile } = useSidebar()
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="fixed left-0 right-0 top-0 z-50 flex items-center justify-between border-b bg-background/95 px-4 py-3 backdrop-blur lg:hidden">
      <picture>
        <source
          srcSet={isDark ? '/assets/logo-head-light.webp' : '/assets/logo-head.webp'}
          type="image/webp"
        />
        <img
          src={isDark ? '/assets/logo-head-light.png' : '/assets/logo-head-fallback.png'}
          alt="Logo"
          className="h-7 w-auto"
        />
      </picture>
      <Button variant="ghost" size="icon" onClick={() => setOpenMobile(!openMobile)}>
        <PanelLeft className="h-4 w-4" />
      </Button>
    </div>
  )
}

export default function DashboardLayout() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="flex-1">
        <MobileHeader />
        <div className="p-4 pt-16 lg:p-8 lg:pt-8">
          <Outlet />
        </div>
      </main>
    </SidebarProvider>
  )
}
