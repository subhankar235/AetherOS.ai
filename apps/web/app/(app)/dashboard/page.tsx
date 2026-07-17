import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { emails, type Priority, type Category } from "@/lib/mock-data";
import { AlertCircle, Circle, Mail, Search, Zap } from "lucide-react";

const priorityColor: Record<Priority, string> = {
  high: "bg-destructive/20 text-destructive border-destructive/30",
  medium: "bg-accent/20 text-accent border-accent/30",
  low: "bg-muted text-muted-foreground border-border",
};

const categoryLabel: Record<Category, string> = {
  investor: "Investor",
  customer: "Customer",
  team: "Team",
  newsletter: "Newsletter",
  billing: "Billing",
  personal: "Personal",
};

export default function Dashboard() {
  const unread = emails.filter((e) => e.unread).length;
  const high = emails.filter((e) => e.priority === "high").length;
  const urgent = emails.filter((e) => e.urgent).length;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Inbox</h1>
          <p className="text-sm text-muted-foreground">
            Silent triage · live updates via Gmail webhook
          </p>
        </div>
        <Link
          href="/command"
          className="inline-flex h-8 items-center justify-center gap-1.5 rounded-lg bg-primary px-2.5 text-sm font-medium text-primary-foreground whitespace-nowrap transition-all hover:bg-primary/80"
        >
          <Zap className="h-4 w-4" /> Command Aether
        </Link>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <Stat label="Unread today" value={unread} icon={<Mail className="h-4 w-4" />} />
        <Stat label="High priority" value={high} icon={<AlertCircle className="h-4 w-4 text-destructive" />} />
        <Stat label="Urgent" value={urgent} icon={<Zap className="h-4 w-4 text-accent" />} />
        <Stat label="Auto-categorized" value={emails.length} icon={<Circle className="h-4 w-4" />} />
      </div>

      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Search inbox…" className="pl-8" />
        </div>
        <Button variant="outline" size="sm">All</Button>
        <Button variant="outline" size="sm">High priority</Button>
        <Button variant="outline" size="sm">Unread</Button>
      </div>

      <Card className="divide-y divide-border overflow-hidden p-0">
        {emails.map((e) => (
          <Link
            key={e.id}
            href={`/inbox/${e.id}`}
            className="flex items-start gap-3 px-4 py-3 transition-colors hover:bg-sidebar-accent"
          >
            <div className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-primary" style={{ opacity: e.unread ? 1 : 0.2 }} />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="truncate text-sm font-medium">{e.from}</span>
                <Badge variant="outline" className="text-[10px]">
                  {categoryLabel[e.category]}
                </Badge>
                <Badge className={`text-[10px] ${priorityColor[e.priority]}`} variant="outline">
                  {e.priority}
                </Badge>
                {e.urgent && (
                  <Badge className="bg-destructive/20 text-destructive border-destructive/30 text-[10px]" variant="outline">
                    urgent
                  </Badge>
                )}
                <span className="ml-auto text-xs text-muted-foreground">
                  {new Date(e.receivedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
              <div className="mt-0.5 truncate text-sm">{e.subject}</div>
              <div className="mt-0.5 truncate text-xs text-muted-foreground">
                <span className="text-primary">AI summary:</span> {e.summary}
              </div>
            </div>
          </Link>
        ))}
      </Card>
    </div>
  );
}

function Stat({ label, value, icon }: { label: string; value: number; icon: React.ReactNode }) {
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>{label}</span>
        {icon}
      </div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </Card>
  );
}
