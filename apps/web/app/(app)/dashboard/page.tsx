"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AlertCircle, Circle, Mail, Search, Zap, RefreshCw } from "lucide-react";

interface RealEmail {
  id: string;
  gmail_message_id: string;
  sender: string;
  subject: string;
  summary?: string;
  priority: string;
  category: string;
  received_at: string;
}

interface SummaryData {
  total_emails: number;
  high_priority: number;
  unread: number;
  recent_meetings: number;
  pending_approvals: number;
}

export default function Dashboard() {
  const { getToken } = useAuth();
  const [emails, setEmails] = useState<RealEmail[]>([]);
  const [summary, setSummary] = useState<SummaryData>({
    total_emails: 0,
    high_priority: 0,
    unread: 0,
    recent_meetings: 0,
    pending_approvals: 0,
  });
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "high">("all");
  const [searchTerm, setSearchTerm] = useState("");

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchDashboardData = async (skipAutoSync = false) => {
    setLoading(true);
    try {
      const token = await getToken();
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      } else {
        headers["Authorization"] = `Bearer dev-token-nathsubhankar57@gmail.com`;
      }

      // 1. Fetch Summary
      const summaryRes = await fetch(`${API_URL}/dashboard/summary`, { headers });
      if (summaryRes.ok) {
        const summaryJson = await summaryRes.json();
        setSummary(summaryJson);
      }

      // 2. Fetch Real Inbox Emails from API
      let emailsRes = await fetch(`${API_URL}/inbox/emails?limit=50`, { headers });
      let emailsJson: RealEmail[] = [];
      if (emailsRes.ok) {
        emailsJson = await emailsRes.json();
      }

      // 3. Auto-sync from Gmail if no emails found and not a manual refresh
      if (emailsJson.length === 0 && !skipAutoSync) {
        await fetch(`${API_URL}/inbox/recent?hours=24`, { headers });
        emailsRes = await fetch(`${API_URL}/inbox/emails?limit=50`, { headers });
        if (emailsRes.ok) {
          emailsJson = await emailsRes.json();
        }
      }

      setEmails(emailsJson);
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const filteredEmails = emails.filter((e) => {
    if (filter === "high" && e.priority !== "High") return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      return (
        (e.sender && e.sender.toLowerCase().includes(q)) ||
        (e.subject && e.subject.toLowerCase().includes(q)) ||
        (e.summary && e.summary.toLowerCase().includes(q))
      );
    }
    return true;
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Inbox</h1>
          <p className="text-sm text-muted-foreground">
            Live email sync from Gmail API
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchDashboardData(true)}
            disabled={loading}
            className="gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
          </Button>
          <Link
            href="/command"
            className="inline-flex h-8 items-center justify-center gap-1.5 rounded-lg bg-primary px-2.5 text-sm font-medium text-primary-foreground whitespace-nowrap transition-all hover:bg-primary/80"
          >
            <Zap className="h-4 w-4" /> Command Aether
          </Link>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <Stat label="Total Emails" value={summary.total_emails || emails.length} icon={<Mail className="h-4 w-4" />} />
        <Stat label="High Priority" value={summary.high_priority} icon={<AlertCircle className="h-4 w-4 text-destructive" />} />
        <Stat label="Unread / Synced" value={summary.unread || emails.length} icon={<Zap className="h-4 w-4 text-accent" />} />
        <Stat label="Live Inbox Items" value={emails.length} icon={<Circle className="h-4 w-4" />} />
      </div>

      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search fetched emails…"
            className="pl-8"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Button
          variant={filter === "all" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("all")}
        >
          All ({emails.length})
        </Button>
        <Button
          variant={filter === "high" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("high")}
        >
          High priority
        </Button>
      </div>

      <Card className="divide-y divide-border overflow-hidden p-0">
        {loading && emails.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted-foreground">
            Loading live emails from Gmail API...
          </div>
        ) : filteredEmails.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted-foreground">
            No fetched emails found. Click "Command Aether" or issue an email search command to sync your Gmail.
          </div>
        ) : (
          filteredEmails.map((e) => (
            <div
              key={e.id}
              className="flex items-start gap-3 px-4 py-3 transition-colors hover:bg-sidebar-accent"
            >
              <div className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-primary" />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate text-sm font-medium">{e.sender}</span>
                  <Badge variant="outline" className="text-[10px]">
                    {e.category || "General"}
                  </Badge>
                  <Badge
                    className={`text-[10px] ${
                      e.priority === "High"
                        ? "bg-destructive/20 text-destructive border-destructive/30"
                        : "bg-accent/20 text-accent border-accent/30"
                    }`}
                    variant="outline"
                  >
                    {e.priority || "Medium"}
                  </Badge>
                  <span className="ml-auto text-xs text-muted-foreground">
                    {e.received_at ? new Date(e.received_at).toLocaleString([], { dateStyle: "short", timeStyle: "short" }) : ""}
                  </span>
                </div>
                <div className="mt-0.5 truncate text-sm font-medium">{e.subject || "(no subject)"}</div>
                {e.summary && (
                  <div className="mt-0.5 truncate text-xs text-muted-foreground">
                    <span className="text-primary font-medium">Summary:</span> {e.summary}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
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
