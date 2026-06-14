import { Tooltip as TooltipPrimitive } from "@base-ui/react/tooltip"
import type { ComponentProps, ReactElement } from "react"

import { cn } from "@/lib/utils"

function TooltipProvider({
  delay = 400,
  ...props
}: ComponentProps<typeof TooltipPrimitive.Provider>) {
  return <TooltipPrimitive.Provider delay={delay} {...props} />
}

function Tooltip({
  children,
  ...props
}: ComponentProps<typeof TooltipPrimitive.Root>) {
  return <TooltipPrimitive.Root {...props}>{children}</TooltipPrimitive.Root>
}

function TooltipTrigger({
  render,
  ...props
}: ComponentProps<typeof TooltipPrimitive.Trigger> & {
  render?: ReactElement
}) {
  return <TooltipPrimitive.Trigger render={render} {...props} />
}

type TooltipContentProps = ComponentProps<typeof TooltipPrimitive.Popup> & {
  side?: "top" | "right" | "bottom" | "left"
  sideOffset?: number
  align?: "start" | "center" | "end"
  hidden?: boolean
}

function TooltipContent({
  className,
  sideOffset,
  children,
  hidden,
  side,
  align,
  ...props
}: TooltipContentProps) {
  if (hidden) return null

  return (
    <TooltipPrimitive.Portal>
      <TooltipPrimitive.Positioner side={side} sideOffset={sideOffset} align={align}>
        <TooltipPrimitive.Popup
          className={cn(
            "z-50 origin-(--anchor-side) overflow-hidden rounded-md border bg-popover px-3 py-1.5 text-xs text-popover-foreground shadow-md animate-in fade-in-0 zoom-in-95",
            className,
          )}
          {...props}
        >
          {children}
        </TooltipPrimitive.Popup>
      </TooltipPrimitive.Positioner>
    </TooltipPrimitive.Portal>
  )
}

export { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger }
