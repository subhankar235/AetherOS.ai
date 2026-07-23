"use client"

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Sparkles, ShieldCheck, Loader2, RotateCw } from "lucide-react";

interface DraftItem {
  id: string;
  email_id?: string;
  body: string;
  version_history?: any[];
  status: string;
  created_at?: string;
  recipient?: string;
  subject?: string;
  original_body?: string;
  original_received_at?: string;
}

export default function RepliesPage() {
  const { getToken, isLoaded } = useAuth();
  const [drafts, setDrafts] = useState<DraftItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);

  const getHeaders = async () => {
    const token = await getToken();
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    } else {
      headers["Authorization"] = `Bearer dev-token-nathsubhankar57@gmail.com`;
    }
    return headers;
  };

  const fetchDrafts = async () => {
    let cached: DraftItem[] = [];
    try {
      cached = JSON.parse(localStorage.getItem("active_drafts_cache") || "[]");
    } catch (e) {}

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = await getHeaders();
      const res = await fetch(`${apiUrl}/replies/drafts`, { headers });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setDrafts(data);
          localStorage.setItem("active_drafts_cache", JSON.stringify(data));
          return;
        }
      }
    } catch (err) {
      console.error("Error fetching drafts from API:", err);
    }

    if (cached.length > 0) {
      setDrafts(cached);
    } else {
      setDrafts([]);
    }
  };

  useEffect(() => {
    fetchDrafts().finally(() => setLoading(false));

    const onFocus = () => fetchDrafts();
    window.addEventListener("focus", onFocus);
    const interval = setInterval(() => fetchDrafts(), 4000);

    return () => {
      window.removeEventListener("focus", onFocus);
      clearInterval(interval);
    };
  }, [isLoaded]);

  const handleEdit = async (draftId: string, instruction: string, currentBody: string) => {
    setEditingId(draftId);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = await getHeaders();
      const res = await fetch(`${apiUrl}/replies/drafts/${draftId}/edit`, {
        method: "POST",
        headers,
        body: JSON.stringify({ instructions: instruction, current_body: currentBody }),
      });
      if (res.ok) {
        const data = await res.json();
        setDrafts((prev) =>
          prev.map((d) => (d.id === draftId ? { ...d, body: data.body, version_history: data.version_history } : d))
        );
      }
    } catch (err) {
      console.error("Failed to edit draft:", err);
    } finally {
      setEditingId(null);
    }
  };

  const handleApproveAndSend = async (draftId: string, currentBody: string) => {
    setEditingId(draftId);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = await getHeaders();
      
      // 1. Prepare Send (Create Approval request & sync latest manual body)
      const prepRes = await fetch(`${apiUrl}/replies/drafts/${draftId}/prepare-send`, {
        method: "POST",
        headers,
        body: JSON.stringify({ current_body: currentBody }),
      });

      if (!prepRes.ok) {
        const errText = await prepRes.text();
        throw new Error(`Prepare send failed: ${errText}`);
      }

      const prepData = await prepRes.json();
      const approvalId = prepData.approval_id;

      // 2. Execute Send with Approval
      const sendRes = await fetch(`${apiUrl}/replies/drafts/${draftId}/send`, {
        method: "POST",
        headers,
        body: JSON.stringify({ approval_id: approvalId }),
      });

      if (sendRes.ok) {
        setDrafts((prev) => prev.filter((d) => d.id !== draftId));
        alert("✅ Email approved and sent successfully via Gmail API!");
      } else {
        const errText = await sendRes.text();
        alert(`Failed to send email: ${errText}`);
      }
    } catch (err: any) {
      console.error("Failed to approve and send draft:", err);
      alert(`Error sending email: ${err.message || err}`);
    } finally {
      setEditingId(null);
    }
  };

  const handleDiscard = async (draftId: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = await getHeaders();
      await fetch(`${apiUrl}/replies/drafts/${draftId}`, { method: "DELETE", headers });
      setDrafts((prev) => prev.filter((d) => d.id !== draftId));
      try {
        const cached = JSON.parse(localStorage.getItem("active_drafts_cache") || "[]");
        localStorage.setItem("active_drafts_cache", JSON.stringify(cached.filter((d: any) => d.id !== draftId)));
      } catch (e) {}
    } catch (err) {
      console.error("Failed to discard draft:", err);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Reply Drafts</h1>
          <p className="text-sm text-muted-foreground">
            Every draft waits behind an approval gate. Review the original email, edit the draft, and click Approve & Send.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            setLoading(true);
            fetchDrafts().finally(() => setLoading(false));
          }}
          className="gap-2"
        >
          <RotateCw className="h-4 w-4" /> Refresh Drafts
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : drafts.length === 0 ? (
        <Card className="p-8 text-center text-sm text-muted-foreground">
          No active reply drafts. Use the Command Center or Inbox to generate a reply draft!
        </Card>
      ) : (
        <div className="space-y-6">
          {drafts.map((d) => (
            <Card key={d.id} className="p-6 space-y-4 border-primary/30 shadow-sm">
              <div className="flex items-start justify-between border-b pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-primary" />
                    <span className="text-base font-semibold">Draft Reply to {d.recipient || "Recipient"}</span>
                    <Badge variant="outline" className="border-accent/40 text-accent">
                      <ShieldCheck className="mr-1 h-3 w-3" /> Awaiting Approval
                    </Badge>
                  </div>
                  {d.subject && (
                    <div className="mt-1 text-xs text-muted-foreground font-medium">
                      Subject: <span className="text-foreground font-semibold">{d.subject.startsWith("Re:") ? d.subject : `Re: ${d.subject}`}</span>
                    </div>
                  )}
                </div>
                {d.created_at && (
                  <div className="text-xs text-muted-foreground">
                    {new Date(d.created_at).toLocaleString()}
                  </div>
                )}
              </div>

              {/* ORIGINAL EMAIL DISPLAY BOX */}
              <div className="rounded-lg border bg-muted/40 p-4 space-y-1.5 text-xs">
                <div className="flex items-center justify-between text-muted-foreground font-semibold uppercase tracking-wider text-[10px]">
                  <span>Original Email Received</span>
                  {d.original_received_at && (
                    <span>{new Date(d.original_received_at).toLocaleString([], { dateStyle: "short", timeStyle: "short" })}</span>
                  )}
                </div>
                <div><span className="font-medium text-muted-foreground">From:</span> <span className="font-semibold text-foreground">{d.recipient || "(unknown)"}</span></div>
                <div><span className="font-medium text-muted-foreground">Subject:</span> <span className="font-semibold text-foreground">{d.subject || "(no subject)"}</span></div>
                {d.original_body && (
                  <div className="mt-2 rounded bg-background p-2.5 text-foreground border text-xs leading-relaxed">
                    {d.original_body}
                  </div>
                )}
              </div>

              {/* DRAFT EDIT TEXTAREA */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Generated Reply Body (Editable)
                </label>
                <Textarea
                  value={d.body}
                  onChange={(e) => {
                    const val = e.target.value;
                    setDrafts((prev) => prev.map((item) => (item.id === d.id ? { ...item, body: val } : item)));
                  }}
                  rows={8}
                  className="font-sans text-sm border-primary/40 focus:border-primary"
                />
              </div>

              <div className="flex flex-wrap gap-2 pt-2 border-t">
                <Button
                  size="sm"
                  onClick={() => handleApproveAndSend(d.id, d.body)}
                  disabled={editingId === d.id}
                  className="bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  {editingId === d.id ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : null}
                  Approve & send
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleEdit(d.id, "Shorten this draft while keeping key points", d.body)}
                  disabled={editingId === d.id}
                >
                  Shorten
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleEdit(d.id, "Make the tone warmer and more friendly", d.body)}
                  disabled={editingId === d.id}
                >
                  Make warmer
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleEdit(d.id, "Make the tone formal and executive", d.body)}
                  disabled={editingId === d.id}
                >
                  Make formal
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="ml-auto text-destructive hover:bg-destructive/10"
                  onClick={() => handleDiscard(d.id)}
                >
                  Discard
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
