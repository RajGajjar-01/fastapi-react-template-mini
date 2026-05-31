import { Tooltip } from '@base-ui/react/tooltip'
import { type ComponentProps, type ReactNode } from 'react'
import { cn } from '@/lib/utils'

function TooltipProvider({ delay = 400, ...props }: ComponentProps<typeof Tooltip.Provider>) {
  return <Tooltip.Provider delay={delay} {...props} />
}

function TooltipComponent({ children, ...props }: ComponentProps<typeof Tooltip.Root>) {
  return (
    <Tooltip.Root {...props}>
      <Tooltip.Trigger>
        <span>{children as ReactNode}</span>
      </Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Positioner sideOffset={4}>
          <Tooltip.Popup
            className={cn(
              'z-50 origin-(--anchor-side) overflow-hidden rounded-md border bg-popover px-3 py-1.5 text-xs text-popover-foreground shadow-md animate-in fade-in-0 zoom-in-95',
            )}
          >
            <Tooltip.Arrow className="fill-popover" />
          </Tooltip.Popup>
        </Tooltip.Positioner>
      </Tooltip.Portal>
    </Tooltip.Root>
  )
}

export { TooltipComponent as Tooltip, TooltipProvider }
