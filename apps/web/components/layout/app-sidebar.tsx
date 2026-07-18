"use client"

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUser, UserButton } from "@clerk/nextjs";
import {
  Inbox,
  Mic,
  MessageSquare,
  Calendar,
  BookOpen,
  Search,
  LifeBuoy,
  CreditCard,
  ShieldCheck,
  ScrollText,
  Settings,
  Sparkles,
} from "lucide-react";
import {
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
} from "@/components/ui/sidebar";

const workspace = [
  { title: "Dashboard", url: "/dashboard", icon: Inbox },
  { title: "Command Center", url: "/command", icon: Mic },
];

const agents = [
  { title: "Reply Drafts", url: "/replies", icon: MessageSquare },
  { title: "Calendar", url: "/calendar", icon: Calendar },
  { title: "Knowledge", url: "/knowledge", icon: BookOpen },
  { title: "Research", url: "/research", icon: Search },
  { title: "Support", url: "/support", icon: LifeBuoy },
  { title: "Payments", url: "/payments", icon: CreditCard },
];

const oversight = [
  { title: "Approvals", url: "/approvals", icon: ShieldCheck },
  { title: "Audit Log", url: "/audit", icon: ScrollText },
  { title: "Settings", url: "/settings", icon: Settings },
];

export function AppSidebar() {
  const pathname = usePathname();
  const { user } = useUser();
  const isActive = (url: string) =>
    url === "/dashboard" ? pathname === url : pathname.startsWith(url);

  const renderGroup = (
    label: string,
    items: { title: string; url: string; icon: typeof Inbox }[],
  ) => (
    <SidebarGroup>
      <SidebarGroupLabel>{label}</SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          {items.map((item) => (
            <SidebarMenuItem key={item.url}>
              <SidebarMenuButton asChild isActive={isActive(item.url)}>
                <Link href={item.url} className="flex items-center gap-3">
                  <item.icon className="h-4 w-4" />
                  <span>{item.title}</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <div className="flex items-center gap-3 px-3 py-2 group-data-[state=collapsed]/sidebar:justify-center group-data-[state=collapsed]/sidebar:gap-0 group-data-[state=collapsed]/sidebar:px-0 group-data-[state=collapsed]/sidebar:py-0">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Sparkles className="h-4 w-4" />
          </div>
          <div className="flex flex-col leading-tight group-data-[state=collapsed]/sidebar:hidden">
            <span className="text-sm font-semibold">Aether</span>
            <span className="text-xs text-muted-foreground">Email Assistant</span>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        {renderGroup("Workspace", workspace)}
        {renderGroup("Agents", agents)}
        {renderGroup("Oversight", oversight)}
      </SidebarContent>
      <SidebarFooter>
        <div className="flex items-center gap-3 rounded-md bg-sidebar-accent px-3 py-2.5 group-data-[state=collapsed]/sidebar:justify-center group-data-[state=collapsed]/sidebar:gap-0 group-data-[state=collapsed]/sidebar:bg-transparent group-data-[state=collapsed]/sidebar:px-0 group-data-[state=collapsed]/sidebar:py-0 group-data-[state=collapsed]/sidebar:[&_.cl-userButtonTrigger]:!flex group-data-[state=collapsed]/sidebar:[&_.cl-userButtonTrigger]:!justify-center">
          <UserButton />
          <div className="flex flex-col text-xs leading-tight group-data-[state=collapsed]/sidebar:hidden">
            <span className="font-medium">
              {user?.fullName || user?.emailAddresses?.[0]?.emailAddress || "User"}
            </span>
            <span className="text-muted-foreground">
              {user?.emailAddresses?.[0]?.emailAddress || ""}
            </span>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}