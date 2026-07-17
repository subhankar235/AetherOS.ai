"use client"

import { createContext, useContext, useState, useCallback, cloneElement, type ReactNode, type ReactElement } from "react"
import { PanelLeft } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

interface SidebarContextValue {
  open: boolean
  setOpen: (open: boolean) => void
  toggle: () => void
}

const SidebarContext = createContext<SidebarContextValue | undefined>(undefined)

function useSidebar() {
  const ctx = useContext(SidebarContext)
  if (!ctx) throw new Error("useSidebar must be used within SidebarProvider")
  return ctx
}

function SidebarProvider({ children, className }: { children: ReactNode; className?: string }) {
  const [open, setOpen] = useState(true)
  const toggle = useCallback(() => setOpen((o) => !o), [])
  return (
    <SidebarContext.Provider value={{ open, setOpen, toggle }}>
      <div className={cn("flex min-h-screen", className)}>{children}</div>
    </SidebarContext.Provider>
  )
}

function SidebarTrigger({ className }: { className?: string }) {
  const { open, toggle } = useSidebar()
  return (
    <Button
      variant="ghost"
      size="icon-sm"
      onClick={toggle}
      className={cn("shrink-0 transition-transform duration-200", open ? "" : "rotate-180", className)}
    >
      <PanelLeft className="h-4 w-4" />
    </Button>
  )
}

function Sidebar({
  children,
  className,
  collapsible,
}: {
  children: ReactNode
  className?: string
  collapsible?: "icon" | "none"
}) {
  const { open } = useSidebar()
  return (
    <aside
      data-state={open ? "expanded" : "collapsed"}
      data-collapsible={collapsible}
      className={cn(
        "group/sidebar flex flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground transition-all duration-200 overflow-hidden",
        collapsible === "icon"
          ? open
            ? "w-64"
            : "w-12"
          : "w-64",
        className
      )}
    >
      {children}
    </aside>
  )
}

function SidebarHeader({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("flex h-12 shrink-0 items-center border-b border-sidebar-border px-2 group-data-[state=collapsed]/sidebar:justify-center group-data-[state=collapsed]/sidebar:px-0", className)}>
      {children}
    </div>
  )
}

function SidebarContent({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("flex-1 overflow-hidden p-3", className)}>{children}</div>
}

function SidebarFooter({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("shrink-0 border-t border-sidebar-border p-3 group-data-[state=collapsed]/sidebar:p-0", className)}>
      {children}
    </div>
  )
}

function SidebarGroup({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("mb-5", className)}>{children}</div>
}

function SidebarGroupLabel({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        "px-3 py-2 text-[11px] font-medium uppercase tracking-wider text-sidebar-foreground/50",
        "group-data-[state=collapsed]/sidebar:hidden",
        className
      )}
    >
      {children}
    </div>
  )
}

function SidebarGroupContent({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("space-y-1", className)}>{children}</div>
}

function SidebarMenu({ children, className }: { children: ReactNode; className?: string }) {
  return <nav className={cn("space-y-1", className)}>{children}</nav>
}

function SidebarMenuItem({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("", className)}>{children}</div>
}

function SidebarMenuButton({
  children,
  className,
  isActive,
  asChild,
}: {
  children: ReactNode
  className?: string
  asChild?: boolean
  isActive?: boolean
}) {
  const child = children as ReactElement<{ className?: string; children?: ReactNode }>

  if (asChild) {
    return cloneElement(child as ReactElement<Record<string, unknown>>, {
      ...child.props,
      "data-active": isActive,
      "data-slot": "sidebar-menu-button",
      className: cn(
        "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
        isActive
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
        "group-data-[state=collapsed]/sidebar:justify-center group-data-[state=collapsed]/sidebar:px-0",
        "group-data-[state=collapsed]/sidebar:[&_span]:hidden",
        child.props.className as string,
        className
      ),
    })
  }

  return (
    <a
      data-active={isActive}
      className={cn(
        "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
        isActive
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
        "group-data-[state=collapsed]/sidebar:justify-center group-data-[state=collapsed]/sidebar:px-0",
        className
      )}
    >
      {children}
    </a>
  )
}

export {
  SidebarProvider,
  SidebarTrigger,
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
}
