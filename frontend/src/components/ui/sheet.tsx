"use client"

import { Dialog } from "@base-ui/react/dialog"
import { cva, type VariantProps } from "class-variance-authority"
import { XIcon } from "lucide-react"
import type { ComponentProps, ReactNode } from "react"

import { cn } from "@/lib/utils"

interface SheetProps extends ComponentProps<typeof Dialog.Root> {
  children?: ReactNode
}

function Sheet({ children, ...props }: SheetProps) {
  return <Dialog.Root {...props}>{children}</Dialog.Root>
}

const SheetTrigger = Dialog.Trigger

const SheetClose = Dialog.Close

const SheetPortal = Dialog.Portal

const SheetOverlay = ({
  className,
  ...props
}: ComponentProps<typeof Dialog.Backdrop>) => {
  return (
    <Dialog.Backdrop
      className={cn(
        "fixed inset-0 z-50 bg-black/80 data-open:animate-in data-closed:animate-out data-closed:fade-out-0 data-open:fade-in-0",
        className,
      )}
      {...props}
    />
  )
}

const sheetVariants = cva(
  "fixed z-50 gap-4 bg-background p-6 shadow-lg transition ease-in-out data-open:animate-in data-closed:animate-out data-closed:duration-300 data-open:duration-500",
  {
    variants: {
      side: {
        top: "inset-x-0 top-0 border-b data-closed:slide-out-to-top data-open:slide-in-from-top",
        bottom:
          "inset-x-0 bottom-0 border-t data-closed:slide-out-to-bottom data-open:slide-in-from-bottom",
        left: "inset-y-0 left-0 h-full w-3/4 border-r data-closed:slide-out-to-left data-open:slide-in-from-left sm:max-w-sm",
        right:
          "inset-y-0 right-0 h-full w-3/4 border-l data-closed:slide-out-to-right data-open:slide-in-from-right sm:max-w-sm",
      },
    },
    defaultVariants: {
      side: "right",
    },
  },
)

interface SheetContentProps
  extends ComponentProps<typeof Dialog.Popup>,
    VariantProps<typeof sheetVariants> {
  side?: "top" | "bottom" | "left" | "right"
}

const SheetContent = ({
  side = "right",
  className,
  children,
  ...props
}: SheetContentProps) => {
  return (
    <SheetPortal>
      <SheetOverlay />
      <Dialog.Popup
        className={cn(sheetVariants({ side }), className)}
        {...props}
      >
        {children}
        <Dialog.Close className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-secondary">
          <XIcon className="h-4 w-4" />
          <span className="sr-only">Close</span>
        </Dialog.Close>
      </Dialog.Popup>
    </SheetPortal>
  )
}

const SheetHeader = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      "flex flex-col space-y-2 text-center sm:text-left",
      className,
    )}
    {...props}
  />
)

const SheetFooter = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      "flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2",
      className,
    )}
    {...props}
  />
)

const SheetTitle = ({
  className,
  ...props
}: ComponentProps<typeof Dialog.Title>) => (
  <Dialog.Title
    className={cn("text-lg font-semibold text-foreground", className)}
    {...props}
  />
)

const SheetDescription = ({
  className,
  ...props
}: ComponentProps<typeof Dialog.Description>) => (
  <Dialog.Description
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
)

export {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetOverlay,
  SheetPortal,
  SheetTitle,
  SheetTrigger,
}
