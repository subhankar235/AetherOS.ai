"use client"

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Mail, Search, Send, Clock, RefreshCw, Filter, Sparkles } from "lucide-react";

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

export default function InboxPage() {
  const { getToken } = useAuth();
  const [emails, setEmails] = useState<RealEmail[]>([]);
  const [loading, setLoading] = useState(true);
  
  // AI Command Input & Sidebar Results
  const [commandInput, setCommandInput] = useState("");
  const [commandLoading, setCommandLoading] = useState(false);
  const [sidebarResults, setSidebarResults] = useState<RealEmail[]>([]);
  const [sidebarTitle, setSidebarTitle] = useState<string>("");
  const [selectedEmail, setSelectedEmail] = useState<RealEmail | null>(null);
  const [filterPriority, setFilterPriority] = useState<string>("all");

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchInbox = async (skipAutoSync = false) => {
    setLoading(true);
    try {
      const token = await getToken();
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      } else {
        headers["Authorization"] = `Bearer dev-token-nathsubhankar57@gmail.com`;
      }

      let res = await fetch(`${API_URL}/inbox/emails?limit=50`, { headers });
      let data: RealEmail[] = [];
      if (res.ok) {
        data = await res.json();
      }

      if (data.length === 0 && !skipAutoSync) {
        await fetch(`${API_URL}/inbox/recent?hours=24`, { headers });
        res = await fetch(`${API_URL}/inbox/emails?limit=50`, { headers });
        if (res.ok) {
          data = await res.json();
        }
      }

      setEmails(data);
    } catch (err) {
      console.error("Failed to fetch inbox:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInbox();
  }, []);

  const runAiCommand = async () => {
    if (!commandInput.trim() || commandLoading) return;
    setCommandLoading(true);

    try {
      const token = await getToken();
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      } else {
        headers["Authorization"] = `Bearer dev-token-nathsubhankar57@gmail.com`;
      }

      const formData = new FormData();
      formData.append("command", commandInput);
      formData.append("session_id", crypto.randomUUID());

      const res = await fetch(`${API_URL}/command`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        const items = data.response?.result?.items || [];
        if (items.length > 0) {
          setSidebarResults(items);
          setSidebarTitle(`Command: "${commandInput}"`);
          setSelectedEmail(items[0]);
        } else {
          setSidebarTitle(`Command: "${commandInput}" (No specific matches)`);
        }
        await fetchInbox(true);
      }
    } catch (err) {
      console.error("AI Command failed:", err);
    } finally {
      setCommandLoading(false);
    }
  };

  const displayedEmails = emails.filter((e) => {
    if (filterPriority === "high" && e.priority !== "High") return false;
    return true;
  });

  return (
    <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-[1fr_400px]">
      {/* Main Inbox View */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Inbox Page</h1>
            <p className="text-sm text-muted-foreground">
              All fetched emails from your Gmail account
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={() => fetchInbox(true)} disabled={loading} className="gap-1.5">
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
          </Button>
        </div>

        {/* Integrated AI Quick Command Bar */}
        <Card className="p-3 bg-primary/5 border-primary/30">
          <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-primary">
            <Sparkles className="h-3.5 w-3.5" /> AI Inbox Command Bar
          </div>
          <div className="flex gap-2">
            <Input
              placeholder="e.g. 'give me last 4 hour email' or 'show emails from Naukri'"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runAiCommand()}
              className="text-xs bg-background"
            />
            <Button size="sm" onClick={runAiCommand} disabled={commandLoading || !commandInput.trim()}>
              <Send className={`h-3.5 w-3.5 ${commandLoading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </Card>

        {/* Filter Controls */}
        <div className="flex items-center gap-2">
          <Button
            variant={filterPriority === "all" ? "default" : "outline"}
            size="sm"
            onClick={() => setFilterPriority("all")}
          >
            All ({emails.length})
          </Button>
          <Button
            variant={filterPriority === "high" ? "default" : "outline"}
            size="sm"
            onClick={() => setFilterPriority("high")}
          >
            High Priority
          </Button>
        </div>

        {/* Main Emails List */}
        <Card className="divide-y divide-border overflow-hidden p-0">
          {loading && emails.length === 0 ? (
            <div className="p-8 text-center text-sm text-muted-foreground">
              Loading emails...
            </div>
          ) : displayedEmails.length === 0 ? (
            <div className="p-8 text-center text-sm text-muted-foreground">
              No emails available.
            </div>
          ) : (
            displayedEmails.map((e) => (
              <div
                key={e.id}
                onClick={() => setSelectedEmail(e)}
                className={`flex items-start gap-3 px-4 py-3 transition-colors cursor-pointer hover:bg-sidebar-accent ${
                  selectedEmail?.id === e.id ? "bg-sidebar-accent" : ""
                }`}
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
                      {e.received_at ? new Date(e.received_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}
                    </span>
                  </div>
                  <div className="mt-0.5 truncate text-sm font-medium">{e.subject}</div>
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

      {/* Right Sidebar — Filtered Command Results / Detail Panel */}
      <div className="space-y-4">
        {sidebarResults.length > 0 ? (
          <Card className="p-4 border-primary/40 shadow-md">
            <div className="flex items-center justify-between border-b pb-2 mb-3">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-primary" />
                <span className="text-xs font-semibold text-primary uppercase">Command Results Sidebar</span>
              </div>
              <Badge variant="outline" className="text-[10px]">
                {sidebarResults.length} Items
              </Badge>
            </div>

            <p className="text-xs text-muted-foreground font-medium mb-3">
              {sidebarTitle}
            </p>

            <div className="max-h-[440px] overflow-y-auto space-y-2 pr-1">
              {sidebarResults.map((item, idx) => (
                <div
                  key={item.id || idx}
                  onClick={() => setSelectedEmail(item)}
                  className={`p-3 rounded-lg border text-xs cursor-pointer transition-all ${
                    selectedEmail?.id === item.id ? "bg-primary/10 border-primary" : "bg-card border-border"
                  }`}
                >
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span className="font-semibold truncate">{item.sender}</span>
                    <Badge variant="outline" className="text-[9px]">
                      {item.priority || "Medium"}
                    </Badge>
                  </div>
                  <div className="font-medium text-foreground truncate mb-1">{item.subject}</div>
                  {item.summary && (
                    <p className="text-muted-foreground line-clamp-2 text-[11px]">{item.summary}</p>
                  )}
                </div>
              ))}
            </div>
          </Card>
        ) : (
          <Card className="p-4">
            <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
              Command Results Sidebar
            </div>
            <p className="text-xs text-muted-foreground">
              Enter commands in the top bar like <em>"give me last 4 hour email"</em> to show query results in this sidebar!
            </p>
          </Card>
        )}

        {/* Selected Email Reader Card */}
        {selectedEmail && (
          <Card className="p-4 bg-muted/20 border-primary/30">
            <div className="text-xs font-semibold text-primary uppercase mb-2">
              Email Detail View
            </div>
            <div className="space-y-1.5 text-xs">
              <div><span className="font-medium text-muted-foreground">From:</span> {selectedEmail.sender}</div>
              <div><span className="font-medium text-muted-foreground">Subject:</span> {selectedEmail.subject}</div>
              {selectedEmail.received_at && (
                <div><span className="font-medium text-muted-foreground">Date:</span> {new Date(selectedEmail.received_at).toLocaleString()}</div>
              )}
              {selectedEmail.summary && (
                <div className="mt-2 text-foreground bg-background p-2.5 rounded border text-xs leading-relaxed">
                  <span className="font-semibold text-primary block mb-1">AI Summary:</span>
                  {selectedEmail.summary}
                </div>
              )}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
