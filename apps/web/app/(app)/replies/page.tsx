"use client"

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { drafts as mockDrafts, emails as mockEmails } from "@/lib/mock-data";
import { Sparkles, ShieldCheck, Loader2 } from "lucide-react";

interface DraftItem {
  id: string;
  email_id?: string;
  body: string;
  version_history?: any[];
  status: string;
  created_at?: string;
  recipient?: string;
  subject?: string;
}

export default function RepliesPage() {
  const { getToken } = useAuth();
  const [drafts, setDrafts] = useState<DraftItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);

  const getHeaders = async () => {
    const token = await getToken();
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  };

  const fetchDrafts = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = await getHeaders();
      const res = await fetch(`${apiUrl}/replies/drafts`, { headers });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setDrafts(data);
          return;
        }
      }
    } catch (err) {
      console.warn("Using fallback mock drafts:", err);
    }
    // Fallback mock items
    setDrafts(
      mockDrafts.map((d) => {
        const src = mockEmails.find((e) => e.id === d.emailId);
        return {
          id: d.id,
          email_id: d.emailId,
          body: d.body,
          status: "drafting",
          created_at: d.createdAt,
          recipient: d.to,
          subject: src?.subject || "Subject",
        };
      })
    );
  };

  useEffect(() => {
    fetchDrafts().finally(() => setLoading(false));
  }, []);

  const handleEdit = async (draftId: string, instruction: string) => {
    setEditingId(draftId);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = await getHeaders();
      const res = await fetch(`${apiUrl}/replies/drafts/${draftId}/edit`, {
        method: "POST",
        headers,
        body: JSON.stringify({ instructions: instruction }),
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

  const handleApproveAndSend = async (draftId: string) => {
    setEditingId(draftId);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = await getHeaders();
      // 1. Prepare Send (Create Approval)
      const prepRes = await fetch(`${apiUrl}/replies/drafts/${draftId}/prepare-send`, {
        method: "POST",
        headers,
      });
      if (prepRes.ok) {
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
          alert("Draft approved and sent successfully!");
        }
      }
    } catch (err) {
      console.error("Failed to approve and send draft:", err);
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
    } catch (err) {
      console.error("Failed to discard draft:", err);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Reply Drafts</h1>
        <p className="text-sm text-muted-foreground">
          Every draft waits behind an approval gate. Aether never sends on its own.
        </p>
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
        <div className="space-y-4">
          {drafts.map((d) => (
            <Card key={d.id} className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-primary" />
                    <span className="text-sm font-medium">Draft to {d.recipient || "Recipient"}</span>
                    <Badge variant="outline" className="border-accent/40 text-accent">
                      <ShieldCheck className="mr-1 h-3 w-3" /> Awaiting approval
                    </Badge>
                  </div>
                  {d.subject && (
                    <div className="mt-1 text-xs text-muted-foreground">
                      In reply to: <span className="text-foreground">{d.subject}</span>
                    </div>
                  )}
                </div>
                {d.created_at && (
                  <div className="text-xs text-muted-foreground">
                    {new Date(d.created_at).toLocaleString()}
                  </div>
                )}
              </div>

              <Textarea
                value={d.body}
                onChange={(e) => {
                  const val = e.target.value;
                  setDrafts((prev) => prev.map((item) => (item.id === d.id ? { ...item, body: val } : item)));
                }}
                rows={8}
                className="mt-4 font-sans text-sm"
              />

              <div className="mt-3 flex flex-wrap gap-2">
                <Button
                  size="sm"
                  onClick={() => handleApproveAndSend(d.id)}
                  disabled={editingId === d.id}
                >
                  {editingId === d.id ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : null}
                  Approve & send
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleEdit(d.id, "Shorten this draft while keeping key points")}
                  disabled={editingId === d.id}
                >
                  Shorten
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleEdit(d.id, "Make the tone warmer and more friendly")}
                  disabled={editingId === d.id}
                >
                  Make warmer
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleEdit(d.id, "Make the tone formal and executive")}
                  disabled={editingId === d.id}
                >
                  Make formal
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="ml-auto text-destructive"
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
