"use client"

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { initialTranscript, type CommandTranscript } from "@/lib/mock-data";
import Link from "next/link";
import { Mic, MicOff, Send, Sparkles, Volume2, Mail, Clock, ShieldAlert, FileText, ChevronRight, CheckCircle2 } from "lucide-react";

interface MatchedEmail {
  id?: string;
  gmail_message_id?: string;
  sender: string;
  subject: string;
  summary?: string;
  priority?: string;
  category?: string;
  received_at?: string;
}

export default function CommandCenter() {
  const { getToken } = useAuth();
  const [transcript, setTranscript] = useState<CommandTranscript[]>(initialTranscript);
  const [input, setInput] = useState("");
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [resultType, setResultType] = useState<string>('default');

  const [sessionId] = useState(() => crypto.randomUUID());
  const [loading, setLoading] = useState(false);

  // Dedicated sidebar query results state
  const [queryResults, setQueryResults] = useState<MatchedEmail[]>([]);
  const [queryTitle, setQueryTitle] = useState<string>("");
  const [selectedEmail, setSelectedEmail] = useState<MatchedEmail | null>(null);

  const getHeaders = async () => {
    const token = await getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    } else {
      headers["Authorization"] = `Bearer dev-token-nathsubhankar57@gmail.com`;
    }
    return headers;
  };

  const handleInstantApproveAndSend = async (draftId: string, bodyText: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = await getHeaders();
      headers["Content-Type"] = "application/json";

      const prepRes = await fetch(`${apiUrl}/replies/drafts/${draftId}/prepare-send`, {
        method: "POST",
        headers,
        body: JSON.stringify({ current_body: bodyText }),
      });
      if (!prepRes.ok) throw new Error("Prepare send failed");
      const prepData = await prepRes.json();

      const sendRes = await fetch(`${apiUrl}/replies/drafts/${draftId}/send`, {
        method: "POST",
        headers,
        body: JSON.stringify({ approval_id: prepData.approval_id }),
      });
      if (sendRes.ok) {
        try {
          const existing = JSON.parse(localStorage.getItem("active_drafts_cache") || "[]");
          const updated = existing.filter((d: any) => d.id !== draftId);
          localStorage.setItem("active_drafts_cache", JSON.stringify(updated));
        } catch (e) {}
        alert("✅ Draft approved and sent successfully via Gmail API!");
      } else {
        const errTxt = await sendRes.text();
        alert(`Failed to send email: ${errTxt}`);
      }
    } catch (err: any) {
      alert(`Error sending draft: ${err.message || err}`);
    }
  };

  const send = async (mode: "voice" | "text") => {
    if (!input.trim() || loading) return;

    const userMessage: CommandTranscript = {
      id: crypto.randomUUID(),
      role: "user",
      mode,
      content: input,
      at: new Date().toISOString(),
    };

    setTranscript((t) => [...t, userMessage]);
    const currentInput = input;
    setInput("");
    setLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = await getHeaders();
      const formData = new FormData();
      formData.append("command", currentInput);
      formData.append("session_id", sessionId);

      const res = await fetch(`${apiUrl}/command`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }

      const data = await res.json();
      const respObj = data.response || {};

      let responseText = "Task completed successfully.";
      
      // Extract matched items for the sidebar panel
      const items: MatchedEmail[] = respObj.result?.items || respObj.context_updates?.last_search_results || [];
      if (items && items.length > 0) {
        setQueryResults(items);
        setQueryTitle(`Command Results: "${currentInput}"`);
        setSelectedEmail(items[0]);
      }

      const resultTypeHeader = res.headers.get('X-Result-Type') || 'default';
      setResultType(resultTypeHeader);

      if (respObj.result?.message) {
        responseText = respObj.result.message;
      } else if (respObj.status === "clarification_needed") {
        responseText = respObj.result?.clarification || "Could you please clarify your request?";
      } else if (respObj.result?.summary) {
        responseText = respObj.result.summary;
      } else if (respObj.result?.answer) {
        responseText = respObj.result.answer;
      } else if (typeof respObj.result === "string") {
        responseText = respObj.result;
      }

      const draftId = respObj.result?.draft_id || respObj.context_updates?.active_draft_id;
      const draftBody = respObj.result?.draft_body || respObj.context_updates?.active_draft_body;

      if (draftId && draftBody) {
        try {
          const newDraftObj = {
            id: draftId,
            body: draftBody,
            status: "drafting",
            created_at: new Date().toISOString(),
            recipient: respObj.result?.target_email?.sender || items[0]?.sender || "Recipient",
            subject: respObj.result?.target_email?.subject || items[0]?.subject || "Reply Draft",
            original_body: items[0]?.summary || "Original Email Content",
          };
          const existing = JSON.parse(localStorage.getItem("active_drafts_cache") || "[]");
          const updated = [newDraftObj, ...existing.filter((d: any) => d.id !== draftId)];
          localStorage.setItem("active_drafts_cache", JSON.stringify(updated));
        } catch (err) {
          console.warn("Error saving to active_drafts_cache:", err);
        }
      }

      const reply: CommandTranscript = {
        id: crypto.randomUUID(),
        role: "assistant",
        mode,
        content: responseText,
        agentUsed: respObj.agent || "Supervisor",
        at: new Date().toISOString(),
        draftId: draftId,
        draftBody: draftBody,
      };
      setTranscript((t) => [...t, reply]);
    } catch (err: any) {
      const reply: CommandTranscript = {
        id: crypto.randomUUID(),
        role: "assistant",
        mode,
        content: `Error connecting to AI Supervisor: ${err.message || "Failed to execute command"}`,
        agentUsed: "Supervisor",
        at: new Date().toISOString(),
      };
      setTranscript((t) => [...t, reply]);
    } finally {
      setLoading(false);
      if (mode === "voice") {
        setSpeaking(true);
        setTimeout(() => setSpeaking(false), 1800);
      }
    }
  };

  return (
    <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-[1fr_420px]">
      {/* Main Command & Chat Section */}
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl font-semibold">Command Center</h1>
          <p className="text-sm text-muted-foreground">
            Talk to Aether — voice or text commands route to AI agents.
          </p>
        </div>

        <Card className="flex flex-col items-center justify-center gap-4 p-8">
          <div className="relative">
            <div
              className={`h-36 w-36 rounded-full bg-gradient-to-br from-primary via-primary/70 to-accent transition-all ${
                speaking ? "scale-105 shadow-[0_0_60px_var(--color-primary)]" : ""
              } ${listening ? "animate-pulse" : ""}`}
            />
            <div className="absolute inset-0 flex items-center justify-center">
              <Sparkles className="h-10 w-10 text-primary-foreground" />
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm font-medium">
              {speaking ? "Speaking…" : listening ? "Listening…" : "Idle — say \"Hey Aether\""}
            </div>
            <div className="text-xs text-muted-foreground">
              Voice: ElevenLabs · Route: Supervisor
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant={listening ? "destructive" : "default"}
              onClick={() => setListening((v) => !v)}
            >
              {listening ? <MicOff className="mr-1.5 h-4 w-4" /> : <Mic className="mr-1.5 h-4 w-4" />}
              {listening ? "Stop" : "Talk to Aether"}
            </Button>
            <Button variant="outline" onClick={() => setSpeaking((v) => !v)}>
              <Volume2 className="mr-1.5 h-4 w-4" /> Replay last
            </Button>
          </div>
        </Card>

        <Card className="p-4">
          <div className="mb-3 text-xs font-medium text-muted-foreground">TRANSCRIPT</div>
          <div className="max-h-[420px] space-y-4 overflow-y-auto pr-2">
            {transcript.map((m) => (
              <div
                key={m.id}
                className={`rounded-lg px-4 py-3 text-sm ${
                  m.role === "user"
                    ? "ml-8 bg-secondary"
                    : "mr-8 border border-primary/30 bg-primary/5"
                }`}
              >
                <div className="mb-1 flex items-center gap-2 text-[10px] uppercase tracking-wide text-muted-foreground">
                  <span>{m.role === "user" ? "You" : "Aether"}</span>
                  <Badge variant="outline" className="text-[9px]">
                    {m.mode}
                  </Badge>
                  {m.agentUsed && (
                    <Badge variant="secondary" className="text-[9px]">
                      {m.agentUsed}
                    </Badge>
                  )}
                </div>
                <div className="whitespace-pre-wrap leading-relaxed">{m.content}</div>

                {/* DIRECT ACTION CARD FOR GENERATED DRAFT */}
                {(m.draftId || m.agentUsed === "reply_agent" || m.content.includes("Reply Draft") || m.content.includes("draft")) && m.role === "assistant" && (
                  <div className="mt-3 rounded-lg border border-primary/40 bg-background p-3.5 space-y-2.5 shadow-sm text-xs">
                    <div className="flex items-center justify-between font-semibold">
                      <span className="flex items-center gap-1.5 text-primary">
                        <Sparkles className="h-4 w-4 text-primary" /> Generated Reply Draft
                      </span>
                      <Badge variant="outline" className="text-[10px] border-accent/40 text-accent">
                        Awaiting Approval
                      </Badge>
                    </div>
                    {m.draftBody && (
                      <div className="rounded bg-muted/60 p-2.5 text-xs max-h-32 overflow-y-auto whitespace-pre-wrap border font-sans leading-relaxed">
                        {m.draftBody}
                      </div>
                    )}
                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      <Link href="/replies">
                        <Button size="sm" className="bg-primary text-primary-foreground hover:bg-primary/90 font-semibold text-xs gap-1.5">
                          Open Reply Drafts Page (/replies) <ChevronRight className="h-3.5 w-3.5" />
                        </Button>
                      </Link>
                      {m.draftId && (
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => handleInstantApproveAndSend(m.draftId!, m.draftBody || "")}
                          className="text-xs gap-1"
                        >
                          <CheckCircle2 className="h-3.5 w-3.5 text-accent" /> Approve & Send Now
                        </Button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="mt-3 flex gap-2">
            <Input
              placeholder="Type a command e.g. 'give me last 4 hour email' or 'show emails from Microsoft'"
              value={input}
              disabled={loading}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !loading && send("text")}
            />
            <Button onClick={() => send("text")} disabled={loading || !input.trim()}>
              <Send className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </Card>
      </div>

      {/* Right Sidebar — Dynamic Command Results Panel */}
      <div className="space-y-4">
        {queryResults.length > 0 ? (
          <Card className="p-4 border-primary/40 shadow-lg">
            <div className="flex items-center justify-between border-b pb-2 mb-3">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-primary" />
                <span className="text-xs font-semibold text-primary uppercase tracking-wider">
                  Command Result Sidebar
                </span>
              </div>
              <Badge variant="outline" className="text-[10px]">
                {queryResults.length} Items
              </Badge>
            </div>
            
            <div className="text-xs text-muted-foreground mb-3 font-medium flex items-center gap-2">
              <span>{queryTitle}</span>
              <Badge variant="outline" className="text-[10px]">{resultType}</Badge>
            </div>

            <div className="max-h-[480px] overflow-y-auto space-y-2 pr-1">
              {queryResults.map((item, idx) => (
                <div
                  key={item.id || item.gmail_message_id || idx}
                  onClick={() => setSelectedEmail(item)}
                  className={`p-3 rounded-lg border text-xs cursor-pointer transition-all hover:border-primary ${
                    selectedEmail?.id === item.id ? "bg-primary/10 border-primary" : "bg-card border-border"
                  }`}
                >
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span className="font-semibold truncate text-foreground">
                      {item.sender}
                    </span>
                    <Badge variant="outline" className="text-[9px] px-1 py-0">
                      {item.priority || "Medium"}
                    </Badge>
                  </div>
                  <div className="font-medium text-foreground truncate mb-1">
                    {item.subject || "(no subject)"}
                  </div>
                  {item.summary && (
                    <p className="text-muted-foreground line-clamp-2 text-[11px]">
                      {item.summary}
                    </p>
                  )}
                  {item.received_at && (
                    <div className="mt-1 flex items-center gap-1 text-[10px] text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {new Date(item.received_at).toLocaleString([], { dateStyle: "short", timeStyle: "short" })}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {selectedEmail && (
              <div className="mt-3 p-3 bg-muted/40 rounded-lg border text-xs space-y-1">
                <div className="font-semibold text-primary">Selected Email Details:</div>
                <div><span className="text-muted-foreground">From:</span> {selectedEmail.sender}</div>
                <div><span className="text-muted-foreground">Subject:</span> {selectedEmail.subject}</div>
                {selectedEmail.summary && (
                  <div className="mt-1 text-muted-foreground bg-background p-2 rounded border">
                    {selectedEmail.summary}
                  </div>
                )}
              </div>
            )}
          </Card>
        ) : (
          <>
            <Card className="p-4">
              <div className="text-xs font-medium text-muted-foreground">COMMAND RESULTS PANEL</div>
              <p className="mt-2 text-xs text-muted-foreground">
                When you issue an email query command (e.g. <em>"give me last 4 hour email"</em>), the matched email cards will render cleanly right here in this sidebar!
              </p>
            </Card>

            <Card className="p-4">
              <div className="text-xs font-medium text-muted-foreground">TRY THESE COMMANDS</div>
              <div className="mt-3 flex flex-col gap-1.5 text-sm">
                {[
                  "give me last 4 hour email",
                  "show emails from Google",
                  "give me 10 emails",
                  "find emails about Microsoft",
                  "show recent newsletter emails",
                ].map((s) => (
                  <button
                    key={s}
                    onClick={() => setInput(s)}
                    className="flex items-center justify-between rounded-md border border-border px-2.5 py-2 text-left text-xs hover:bg-sidebar-accent hover:border-primary/50 transition-all"
                  >
                    <span>{s}</span>
                    <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
                  </button>
                ))}
              </div>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
