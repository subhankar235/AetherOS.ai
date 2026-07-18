import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { auth } from "@clerk/nextjs/server";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  await auth.protect();
  return (
    <SidebarProvider>
      <div className="flex h-screen w-full overflow-hidden bg-background text-foreground">
        <AppSidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-10 flex h-12 items-center gap-2 border-b border-border bg-background/80 px-3 backdrop-blur">
            <SidebarTrigger />
            <span className="text-xs text-muted-foreground">Aether · workspace</span>
          </header>
          <main className="flex-1 overflow-y-auto p-6">
            {children}
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}