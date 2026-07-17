"use client"

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { initialTranscript, type CommandTranscript } from "@/lib/mock-data";
import { Mic, MicOff, Send, Sparkles, Volume2 } from "lucide-react";

export default function CommandCenter() {
  const [transcript, setTranscript] = useState<CommandTranscript[]>(initialTranscript);
  const [input, setInput] = useState("");
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);

  const send = (mode: "voice" | "text") => {
    if (!input.trim()) return;
    const userMsg: CommandTranscript = {
      id: crypto.randomUUID(),
      role: "user",
      mode,
      content: input,
      at: new Date().toISOString(),
    };
    const reply: CommandTranscript = {
      id: crypto.randomUUID(),
      role: "assistant",
      mode,
      content:
        "Got it — routing that to the right agent. I'll show the result here and ask before doing anything consequential.",
      agentUsed: "Supervisor",
      at: new Date().toISOString(),
    };
    setTranscript((t) => [...t, userMsg, reply]);
    setInput("");
    if (mode === "voice") {
      setSpeaking(true);
      setTimeout(() => setSpeaking(false), 1800);
    }
  };

  return (
    <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-[1fr_360px]">
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl font-semibold">Command Center</h1>
          <p className="text-sm text-muted-foreground">
            Talk to Aether — by voice or text. Supervisor routes to the right agent.
          </p>
        </div>

        <Card className="flex flex-col items-center justify-center gap-4 p-8">
          <div className="relative">
            <div
              className={`h-40 w-40 rounded-full bg-gradient-to-br from-primary via-primary/70 to-accent transition-all ${
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
          <div className="max-h-[420px] space-y-3 overflow-y-auto pr-2">
            {transcript.map((m) => (
              <div
                key={m.id}
                className={`rounded-lg px-3 py-2 text-sm ${
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
                {m.content}
              </div>
            ))}
          </div>

          <div className="mt-3 flex gap-2">
            <Input
              placeholder="Type a command, e.g. 'Reply to Sarah and keep it warm'"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send("text")}
            />
            <Button onClick={() => send("text")}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      </div>

      <div className="space-y-4">
        <Card className="p-4">
          <div className="text-xs font-medium text-muted-foreground">HUMAN VOICE LAYER</div>
          <ul className="mt-3 space-y-2 text-sm">
            <li className="flex items-start gap-2">
              <span className="mt-0.5 h-4 w-4 shrink-0 rounded-full bg-primary/30" /> Conversational rewrite (GPT-5.5)
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5 h-4 w-4 shrink-0 rounded-full bg-primary/30" /> Tone adaptation
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5 h-4 w-4 shrink-0 rounded-full bg-primary/30" /> ElevenLabs TTS
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5 h-4 w-4 shrink-0 rounded-full bg-primary/30" /> Avatar mouth sync
            </li>
          </ul>
        </Card>
        <Card className="p-4">
          <div className="text-xs font-medium text-muted-foreground">SUGGESTED COMMANDS</div>
          <div className="mt-3 flex flex-col gap-1.5 text-sm">
            {[
              "What came in from investors this week?",
              "Draft a reply to Marcus about the renewal",
              "Schedule Sequoia for Thursday 3pm",
              "Answer using our refund policy",
              "Report on BigCo before I reply",
            ].map((s) => (
              <button
                key={s}
                onClick={() => setInput(s)}
                className="rounded-md border border-border px-2.5 py-1.5 text-left text-xs hover:bg-sidebar-accent"
              >
                {s}
              </button>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
