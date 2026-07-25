"use client"

import { useState, useEffect, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { type CommandTranscript } from "@/lib/mock-data";
import Link from "next/link";
import { Mic, MicOff, Send, Sparkles, Volume2, Mail, Clock, ShieldAlert, FileText, ChevronRight, CheckCircle2, AlertTriangle, Trash2, RefreshCw, Video, Calendar as CalendarIcon } from "lucide-react";

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

interface ActiveDraftInfo {
  draft_id: string;
  draft_body: string;
  has_gaps?: boolean;
  gap_notes?: string[];
  recipient?: string;
  subject?: string;
  created_at?: string;
}

interface ActiveCalendarProposalInfo {
  preview_id: string;
  approval_id?: string;
  title: string;
  start: string;
  end: string;
  duration_minutes?: number;
  attendees?: string[];
  meet_link?: string;
  target_email?: {
    subject?: string;
    sender?: string;
    id?: string;
  };
  source_email?: {
    subject?: string;
    from?: { name?: string; email?: string };
    summary?: string;
    message_id?: string;
  };
  double_booking_warnings?: any[];
}

export default function CommandCenter() {
  const { getToken } = useAuth();
  const [transcript, setTranscript] = useState<CommandTranscript[]>([]);
  const [input, setInput] = useState("");
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [resultType, setResultType] = useState<string>('default');

  const [sessionId] = useState(() => crypto.randomUUID());
  const [loading, setLoading] = useState(false);
  const [isCallActive, setIsCallActive] = useState(false);
  const recognitionRef = useRef<any>(null);
  const callActiveRef = useRef(false); // tracks call state across async closures
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null); // tracks current speech for interruption
  const audioRef = useRef<HTMLAudioElement | null>(null); // ElevenLabs audio playback element
  const inputRef = useRef(""); // mirrors input state to avoid stale closures
  const recognitionGenRef = useRef(0); // generation counter to prevent stale handler loops

  // Dedicated sidebar query results state
  const [queryResults, setQueryResults] = useState<MatchedEmail[]>([]);
  const [queryTitle, setQueryTitle] = useState<string>("");
  const [selectedEmail, setSelectedEmail] = useState<MatchedEmail | null>(null);

  // Dedicated sidebar active draft result state
  const [activeDraft, setActiveDraft] = useState<ActiveDraftInfo | null>(null);

  // Dedicated sidebar active calendar proposal state
  const [activeProposal, setActiveProposal] = useState<ActiveCalendarProposalInfo | null>(null);

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

  // Fetch real active AI drafts and calendar proposals from backend on page load
  const loadLatestBackendData = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = await getHeaders();

      // 1. Load active email drafts
      const res = await fetch(`${apiUrl}/replies/drafts`, { headers });
      if (res.ok) {
        const drafts = await res.json();
        if (Array.isArray(drafts) && drafts.length > 0) {
          const latest = drafts[0];
          setActiveDraft({
            draft_id: latest.id || latest.draft_id,
            draft_body: latest.body || latest.current_body,
            has_gaps: latest.has_gaps || false,
            gap_notes: latest.gap_notes || [],
            recipient: latest.recipient || "Recipient",
            subject: latest.subject || "Reply Draft",
            created_at: latest.created_at,
          });
        }
      }

      // 2. Load active calendar proposals
      const meetRes = await fetch(`${apiUrl}/calendar/meetings`, { headers });
      if (meetRes.ok) {
        const meetings = await meetRes.json();
        if (Array.isArray(meetings)) {
          const pending = meetings.find((m: any) => m.status === "previewed");
          if (pending && pending.proposed_slots && pending.proposed_slots.length > 0) {
            const slot = pending.proposed_slots[0];
            setActiveProposal({
              preview_id: pending.id,
              title: slot.title || "Meeting Proposal",
              start: slot.start,
              end: slot.end,
              duration_minutes: slot.duration_minutes || 60,
              attendees: (pending.participants || []).map((p: any) => p.email || p.displayName || p),
              meet_link: pending.hangout_link || pending.meet_link || "https://meet.google.com/abc-defg-hij",
            });
          }
        }
      }
    } catch (err) {
      console.warn("Failed to load initial backend data:", err);
    }
  };

  useEffect(() => {
    loadLatestBackendData();
  }, []);

  const handleInstantConfirmCalendarEvent = async (previewId: string, approvalId?: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = await getHeaders();
      headers["Content-Type"] = "application/json";

      const res = await fetch(`${apiUrl}/calendar/confirm`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          approval_id: approvalId || previewId,
          preview_id: previewId,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        let msg = `✅ Calendar event confirmed & created!`;
        if (data.meet_link || data.hangout_link) {
          msg += `\n🎥 Meet Link: ${data.meet_link || data.hangout_link}`;
        }
        if (data.invitation_sent) {
          msg += `\n📧 Invitation email sent successfully!`;
        } else if (data.invitation_error) {
          msg += `\n⚠️ Invitation notice: ${data.invitation_error}`;
        } else {
          msg += `\n⚠️ Invitation notice: Google Account missing email send scope. Reconnect Google in Settings -> Integrations to enable automatic email dispatch.`;
        }
        alert(msg);
        setActiveProposal(null);
      } else {
        const errTxt = await res.text();
        alert(`Failed to confirm event: ${errTxt}`);
      }
    } catch (err: any) {
      alert(`Error confirming calendar event: ${err.message || err}`);
    }
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
        if (activeDraft?.draft_id === draftId) {
          setActiveDraft(null);
        }
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

      if (respObj.result?.meeting) {
        const meetingSchema = {
          status: respObj.result.status || "success",
          message: respObj.result.message || "Meeting scheduled successfully.",
          meeting: respObj.result.meeting,
        };
        responseText = JSON.stringify(meetingSchema, null, 2);
      } else if (respObj.status === "clarification_needed") {
        responseText = respObj.result?.clarification || "Could you please clarify your request?";
      } else if (respObj.result?.message) {
        responseText = respObj.result.message;
      } else if (respObj.result?.summary) {
        responseText = respObj.result.summary;
      } else if (respObj.result?.answer) {
        responseText = respObj.result.answer;
      } else if (typeof respObj.result === "string") {
        responseText = respObj.result;
      }

      const draftId = respObj.result?.draft_id || respObj.context_updates?.active_draft_id;
      const draftBody = respObj.result?.draft_body || respObj.context_updates?.active_draft_body;
      const hasGaps = respObj.result?.has_gaps ?? respObj.context_updates?.has_gaps ?? false;
      const gapNotes = respObj.result?.gap_notes ?? respObj.context_updates?.gap_notes ?? [];
      const recipient = respObj.result?.target_email?.sender || items[0]?.sender || "Recipient";
      const subject = respObj.result?.target_email?.subject || items[0]?.subject || "Reply Draft";

      if (draftId && draftBody) {
        const draftObj: ActiveDraftInfo = {
          draft_id: draftId,
          draft_body: draftBody,
          has_gaps: hasGaps,
          gap_notes: gapNotes,
          recipient: recipient,
          subject: subject,
        };
        setActiveDraft(draftObj);

        try {
          const newDraftObj = {
            id: draftId,
            body: draftBody,
            status: "drafting",
            created_at: new Date().toISOString(),
            recipient: recipient,
            subject: subject,
            original_body: respObj.result?.target_email?.summary || items[0]?.summary || "",
            has_gaps: hasGaps,
            gap_notes: gapNotes,
          };
          const existing = JSON.parse(localStorage.getItem("active_drafts_cache") || "[]");
          const updated = [newDraftObj, ...existing.filter((d: any) => d.id !== draftId)];
          localStorage.setItem("active_drafts_cache", JSON.stringify(updated));
        } catch (err) {
          console.warn("Error saving to active_drafts_cache:", err);
        }
      }

      const mData = respObj.result?.meeting;
      const sEmailData = respObj.result?.source_email;
      const previewId = mData?.id || respObj.context_updates?.active_calendar_preview_id;
      const approvalId = respObj.context_updates?.active_calendar_approval_id || previewId;
      const meetingStart = mData?.start_time;
      const meetingEnd = mData?.end_time;
      const meetingTitle = mData?.title || "Meeting Proposal";
      const meetLink = mData?.meet_link || "https://meet.google.com/abc-defg-hij";

      if (previewId && meetingStart && meetingEnd) {
        const attendeeEmails = (mData?.attendees || []).map((a: any) => typeof a === "object" ? a.email || a.name : String(a));
        setActiveProposal({
          preview_id: previewId,
          approval_id: approvalId,
          title: meetingTitle,
          start: meetingStart,
          end: meetingEnd,
          duration_minutes: 60,
          attendees: attendeeEmails,
          meet_link: meetLink,
          source_email: sEmailData,
        });

        try {
          const newMeetingObj = {
            id: previewId,
            status: "previewed",
            participants: attendeeEmails.map((e: string) => ({ email: e })),
            proposed_slots: [{ start: meetingStart, end: meetingEnd, title: meetingTitle, meet_link: meetLink }],
            created_at: new Date().toISOString(),
            hangout_link: meetLink,
            meet_link: meetLink,
            source_email: sEmailData,
            meeting: mData,
          };
          const existingM = JSON.parse(localStorage.getItem("active_meetings_cache") || "[]");
          const updatedM = [newMeetingObj, ...existingM.filter((m: any) => m.id !== previewId)];
          localStorage.setItem("active_meetings_cache", JSON.stringify(updatedM));
        } catch (err) {
          console.warn("Error saving to active_meetings_cache:", err);
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
    }
  };
  // ─── VOICE ASSISTANT: Full Implementation ───────────────────────────────

  // Cancel any ongoing speech immediately (interruption support)
  const cancelSpeech = () => {
    // Stop ElevenLabs audio playback
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      // Revoke the blob URL to free memory
      if (audioRef.current.src) {
        URL.revokeObjectURL(audioRef.current.src);
      }
      audioRef.current = null;
    }
    // Also cancel browser speech synthesis as fallback
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    utteranceRef.current = null;
    setSpeaking(false);
  };

  // Speak text aloud via ElevenLabs TTS API, with browser fallback
  // IMPORTANT: Starts listening simultaneously so user can interrupt mid-speech
  const speakText = async (text: string, onDone?: () => void) => {
    if (typeof window === 'undefined') {
      onDone?.();
      return;
    }
    // Cancel any existing speech first
    cancelSpeech();
    setSpeaking(true);

    try {
      // Call our server-side TTS proxy (ElevenLabs)
      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });

      if (!res.ok) throw new Error(`TTS API returned ${res.status}`);

      const audioBlob = await res.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        audioRef.current = null;
        setSpeaking(false);
        onDone?.();
      };
      audio.onerror = () => {
        URL.revokeObjectURL(audioUrl);
        audioRef.current = null;
        setSpeaking(false);
        onDone?.();
      };

      // Check if call was ended before playback started
      if (!callActiveRef.current) {
        URL.revokeObjectURL(audioUrl);
        setSpeaking(false);
        return;
      }

      await audio.play();

      // START LISTENING DURING SPEECH for interruption support
      // User can speak while audio is playing — recognition will fire,
      // cancelSpeech() will stop audio, and new command will be processed
      if (callActiveRef.current) {
        startListeningRound();
      }
    } catch (err) {
      console.warn('ElevenLabs TTS failed, falling back to browser speech:', err);
      // Fallback to browser SpeechSynthesis
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'en-US';
        utterance.rate = 1.05;
        utteranceRef.current = utterance;
        utterance.onend = () => {
          utteranceRef.current = null;
          setSpeaking(false);
          onDone?.();
        };
        utterance.onerror = () => {
          utteranceRef.current = null;
          setSpeaking(false);
          onDone?.();
        };
        window.speechSynthesis.speak(utterance);
        // Also listen during browser speech for interruption
        if (callActiveRef.current) startListeningRound();
      } else {
        setSpeaking(false);
        onDone?.();
      }
    }
  };

  // Start a new SpeechRecognition listening session (one utterance at a time)
  const startListeningRound = () => {
    if (typeof window === 'undefined') return;
    if (!callActiveRef.current) return;
    if (!('SpeechRecognition' in window) && !('webkitSpeechRecognition' in window)) return;

    // Increment generation — any handlers from previous recognition instances
    // will see a stale generation and NOT restart (prevents infinite abort loops)
    const gen = ++recognitionGenRef.current;

    // Abort any existing recognition (this will fire onerror/onend on OLD instance,
    // but those handlers will check generation and bail)
    if (recognitionRef.current) {
      try { recognitionRef.current.abort(); } catch (e) {}
      recognitionRef.current = null;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.continuous = false;
    recognitionRef.current = recognition;
    setListening(true);

    recognition.onresult = (event: any) => {
      if (gen !== recognitionGenRef.current) return; // stale
      const spokenText = event.results[0][0].transcript;
      // INTERRUPTION: cancel any ongoing speech immediately
      cancelSpeech();
      // Send the user's voice input through the command pipeline
      sendVoiceCommand(spokenText);
    };

    recognition.onerror = (event: any) => {
      if (gen !== recognitionGenRef.current) return; // stale — don't restart
      // Only restart on no-speech (user was silent too long)
      if (callActiveRef.current && event.error === 'no-speech') {
        setTimeout(() => {
          if (callActiveRef.current && gen === recognitionGenRef.current) startListeningRound();
        }, 500);
      }
      // For 'aborted' — do nothing, it was our own intentional abort
      // For other errors — log but don't loop
      if (event.error !== 'no-speech' && event.error !== 'aborted') {
        console.warn('SpeechRecognition error:', event.error);
      }
    };

    recognition.onend = () => {
      if (gen !== recognitionGenRef.current) return; // stale — don't restart
      setListening(false);
      // Auto-restart listening if call is still active
      if (callActiveRef.current) {
        setTimeout(() => {
          if (callActiveRef.current && gen === recognitionGenRef.current) startListeningRound();
        }, 300);
      }
    };

    try {
      recognition.start();
    } catch (e) {
      // Failed to start — retry once after delay
      setTimeout(() => {
        if (callActiveRef.current && gen === recognitionGenRef.current) startListeningRound();
      }, 600);
    }
  };

  // Send a voice command directly (avoids stale closure issues with setInput + send)
  // IMPORTANT: Does NOT block on loading — allows interruption even during processing
  const sendVoiceCommand = async (spokenText: string) => {
    if (!spokenText.trim()) return;

    // If already loading (previous command still processing), cancel it conceptually
    // and proceed with the new command (interruption takes priority)
    setListening(false);

    const userMessage: CommandTranscript = {
      id: crypto.randomUUID(),
      role: "user",
      mode: "voice",
      content: spokenText,
      at: new Date().toISOString(),
    };
    setTranscript((t) => [...t, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = await getHeaders();
      const formData = new FormData();
      formData.append("command", spokenText);
      formData.append("session_id", sessionId);

      const res = await fetch(`${apiUrl}/command`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data = await res.json();
      const respObj = data.response || {};

      let responseText = "Done, Sir.";
      if (respObj.status === "clarification_needed") {
        responseText = respObj.result?.clarification || "Could you clarify that for me?";
      } else if (respObj.result?.message) {
        responseText = respObj.result.message;
      } else if (respObj.result?.summary) {
        responseText = respObj.result.summary;
      } else if (respObj.result?.answer) {
        responseText = respObj.result.answer;
      } else if (typeof respObj.result === "string") {
        responseText = respObj.result;
      }

      // Handle drafts, proposals, sidebar updates (same as text send)
      const items: MatchedEmail[] = respObj.result?.items || respObj.context_updates?.last_search_results || [];
      if (items && items.length > 0) {
        setQueryResults(items);
        setQueryTitle(`Command Results: "${spokenText}"`);
        setSelectedEmail(items[0]);
      }
      const resultTypeHeader = res.headers.get('X-Result-Type') || 'default';
      setResultType(resultTypeHeader);

      const draftId = respObj.result?.draft_id || respObj.context_updates?.active_draft_id;
      const draftBody = respObj.result?.draft_body || respObj.context_updates?.active_draft_body;
      if (draftId && draftBody) {
        setActiveDraft({
          draft_id: draftId,
          draft_body: draftBody,
          has_gaps: respObj.result?.has_gaps ?? false,
          gap_notes: respObj.result?.gap_notes ?? [],
          recipient: respObj.result?.target_email?.sender || items[0]?.sender || "Recipient",
          subject: respObj.result?.target_email?.subject || items[0]?.subject || "Reply Draft",
        });
      }

      const reply: CommandTranscript = {
        id: crypto.randomUUID(),
        role: "assistant",
        mode: "voice",
        content: responseText,
        agentUsed: respObj.agent || "Supervisor",
        at: new Date().toISOString(),
        draftId,
        draftBody,
      };
      setTranscript((t) => [...t, reply]);

      // SPEAK the response aloud, then restart listening
      speakText(responseText, () => {
        if (callActiveRef.current) {
          startListeningRound();
        }
      });
    } catch (err: any) {
      const errorMsg = `Sorry Sir, I couldn't process that. ${err.message || ""}`;
      const reply: CommandTranscript = {
        id: crypto.randomUUID(),
        role: "assistant",
        mode: "voice",
        content: errorMsg,
        agentUsed: "Supervisor",
        at: new Date().toISOString(),
      };
      setTranscript((t) => [...t, reply]);
      speakText(errorMsg, () => {
        if (callActiveRef.current) startListeningRound();
      });
    } finally {
      setLoading(false);
    }
  };

  // Generate a fresh, dynamic greeting WITH Aether identity
  const generateGreeting = (): string => {
    const hour = new Date().getHours();
    const timeGreetings = hour < 12
      ? [
          "Good morning, Sir! I'm Aether, your AI assistant. What can I help you with?",
          "Morning! Aether here. What do you need today?",
          "Hey, good morning! I'm Aether. How can I assist you?",
        ]
      : hour < 17
      ? [
          "Good afternoon! I'm Aether. What can I do for you?",
          "Hey there! Aether here, ready to help. What do you need?",
          "Afternoon, Sir. I'm Aether. What's on your mind?",
        ]
      : [
          "Good evening! I'm Aether. What can I help with?",
          "Evening, Sir. Aether here. Need something?",
          "Hey! I'm Aether, your assistant. How can I help tonight?",
        ];
    return timeGreetings[Math.floor(Math.random() * timeGreetings.length)];
  };

  // Detect if user input is a casual/conversational question (not a command)
  const isConversational = (text: string): boolean => {
    const lower = text.toLowerCase().trim();
    const patterns = [
      /^(hi|hello|hey|yo|sup|hola)/,
      /how are you/,
      /what('?s| is) your name/,
      /who are you/,
      /what can you do/,
      /what do you do/,
      /how can you help/,
      /are you (an? )?(ai|robot|bot|human|real)/,
      /thank(s| you)/,
      /good (morning|afternoon|evening|night)/,
      /bye|goodbye|see you|later/,
      /you('?re| are) (great|awesome|cool|amazing|the best)/,
      /nice to meet/,
      /what('?s| is) up/,
      /how('?s| is) it going/,
      /tell me about yourself/,
    ];
    return patterns.some(p => p.test(lower));
  };

  // Generate a natural conversational response (no backend needed)
  const getConversationalResponse = (text: string): string => {
    const lower = text.toLowerCase().trim();

    if (/how are you|how('?s| is) it going/.test(lower)) {
      const responses = [
        "I'm doing great, Sir! Ready to help you with anything.",
        "All good on my end! What can I do for you?",
        "I'm excellent, thank you for asking! How can I assist?",
      ];
      return responses[Math.floor(Math.random() * responses.length)];
    }
    if (/what('?s| is) your name|who are you|tell me about yourself/.test(lower)) {
      return "I'm Aether, your AI assistant from AetherOS. I can manage your emails, schedule meetings, draft replies, and help with anything you need. Just tell me what to do!";
    }
    if (/what can you do|what do you do|how can you help/.test(lower)) {
      return "I can check your emails, draft replies, schedule meetings, and handle tasks for you. Just tell me what you need, Sir, and I'll take care of it.";
    }
    if (/are you (an? )?(ai|robot|bot)/.test(lower)) {
      return "I'm Aether, your personal AI assistant. I'm here to get things done for you. What do you need?";
    }
    if (/thank/.test(lower)) {
      const responses = [
        "You're welcome, Sir! Anything else?",
        "Happy to help! Need anything else?",
        "Anytime! What's next?",
      ];
      return responses[Math.floor(Math.random() * responses.length)];
    }
    if (/bye|goodbye|see you|later/.test(lower)) {
      return "Goodbye, Sir! I'll be here whenever you need me.";
    }
    if (/^(hi|hello|hey|yo|sup|hola)|good (morning|afternoon|evening)|nice to meet/.test(lower)) {
      const responses = [
        "Hey! I'm Aether. What can I help you with?",
        "Hi there! Ready to help. What do you need?",
        "Hello, Sir! What can I do for you?",
      ];
      return responses[Math.floor(Math.random() * responses.length)];
    }
    if (/you('?re| are) (great|awesome|cool|amazing|the best)/.test(lower)) {
      return "Thank you, Sir! Always happy to help. What's next?";
    }
    return "I'm here to help! Just tell me what you need.";
  };

  // Summarize a backend response for SHORT spoken output (don't read everything)
  const summarizeForSpeech = (fullText: string, spokenText: string): string => {
    // If response is already short (under 80 chars), speak it as-is
    if (fullText.length < 80) return fullText;

    // Count items in list-style responses
    const itemMatches = fullText.match(/\d+\.\s\*\*/g) || fullText.match(/Found \d+ email/);
    if (itemMatches) {
      const countMatch = fullText.match(/Found (\d+) email/);
      if (countMatch) {
        return `Done Sir, I found ${countMatch[1]} emails for you. The results are in the sidebar. Want me to read them out?`;
      }
      const listCount = (fullText.match(/\d+\.\s\*\*/g) || []).length;
      if (listCount > 0) {
        return `Done Sir, I got ${listCount} results for you. They're in the sidebar. Want me to read them?`;
      }
    }

    // Draft responses
    if (fullText.toLowerCase().includes('draft') || fullText.toLowerCase().includes('reply')) {
      return "Done Sir, I've drafted the reply for you. You can review it in the sidebar. Want me to read it out?";
    }

    // Meeting/calendar responses
    if (fullText.toLowerCase().includes('meeting') || fullText.toLowerCase().includes('calendar') || fullText.toLowerCase().includes('scheduled')) {
      return "Done Sir, I've set that up for you. The details are in the sidebar. Anything else?";
    }

    // Generic long response — truncate to first sentence
    const firstSentence = fullText.split(/[.!?]\s/)[0];
    if (firstSentence && firstSentence.length < 150) {
      return firstSentence + ". Want me to read more details?";
    }

    return "Done Sir, I've completed that for you. The details are shown on screen. Want me to read them out?";
  };

  // ─── ONE BUTTON: Start / Stop the voice call ──────────────────────────
  const startTalkToAetherCall = () => {
    if (typeof window === 'undefined') return;
    if (!('SpeechRecognition' in window) && !('webkitSpeechRecognition' in window)) {
      alert('Speech Recognition is not supported in this browser. Please use Chrome.');
      return;
    }
    callActiveRef.current = true;
    setIsCallActive(true);

    // Fresh greeting spoken aloud
    const greeting = generateGreeting();
    const greetMsg: CommandTranscript = {
      id: crypto.randomUUID(),
      role: "assistant",
      mode: "voice",
      content: greeting,
      agentUsed: "Aether",
      at: new Date().toISOString(),
    };
    setTranscript((t) => [...t, greetMsg]);

    // Speak greeting, then start listening
    speakText(greeting, () => {
      if (callActiveRef.current) {
        startListeningRound();
      }
    });
  };

  const endTalkToAetherCall = () => {
    callActiveRef.current = false;
    recognitionGenRef.current++; // invalidate all pending recognition handlers
    setIsCallActive(false);
    setListening(false);
    cancelSpeech();
    if (recognitionRef.current) {
      try { recognitionRef.current.abort(); } catch (e) {}
      recognitionRef.current = null;
    }
  };

  // Cleanup on component unmount
  useEffect(() => {
    return () => {
      callActiveRef.current = false;
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch (e) {}
      }
      cancelSpeech();
    };
  }, []);


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
              className={`h-36 w-36 rounded-full bg-gradient-to-br from-primary via-primary/70 to-accent transition-all duration-300 ${
                speaking ? "scale-110 shadow-[0_0_80px_var(--color-primary)]" : ""
              } ${listening ? "animate-pulse shadow-[0_0_40px_var(--color-primary)]" : ""} ${
                loading ? "animate-spin opacity-70" : ""
              }`}
            />
            <div className="absolute inset-0 flex items-center justify-center">
              {speaking ? (
                <Volume2 className="h-10 w-10 text-primary-foreground animate-pulse" />
              ) : listening ? (
                <Mic className="h-10 w-10 text-primary-foreground" />
              ) : (
                <Sparkles className="h-10 w-10 text-primary-foreground" />
              )}
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm font-medium">
              {speaking ? "Aether is speaking…" : listening ? "Listening to you…" : loading ? "Processing…" : isCallActive ? "Ready — speak anytime" : "Press the button to start"}
            </div>
            {isCallActive && (
              <div className="text-xs text-muted-foreground mt-1">
                Voice session active · Speak naturally
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              size="lg"
              variant={isCallActive ? "destructive" : "default"}
              className="px-8 py-3 text-base font-semibold"
              onClick={() => {
                if (isCallActive) {
                  endTalkToAetherCall();
                } else {
                  startTalkToAetherCall();
                }
              }}
            >
              {isCallActive ? <MicOff className="mr-2 h-5 w-5" /> : <Mic className="mr-2 h-5 w-5" />}
              {isCallActive ? "End Call" : "Talk to Agent"}
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

                {/* DIRECT ACTION CARD FOR CALENDAR PROPOSAL */}
                {(m.agentUsed === "calendar_agent" || m.content.includes("Meeting scheduled successfully") || m.content.includes("meeting") || m.content.includes("Calendar Proposal")) && m.role === "assistant" && (
                  <div className="mt-3 rounded-lg border border-emerald-500/40 bg-emerald-500/5 p-3.5 space-y-2.5 shadow-sm text-xs">
                    <div className="flex items-center justify-between font-semibold">
                      <span className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400">
                        <Sparkles className="h-4 w-4" /> Meeting Scheduled / Proposed
                      </span>
                      <Badge variant="outline" className="text-[10px] border-emerald-500/40 text-emerald-500">
                        Calendar Agent
                      </Badge>
                    </div>

                    {activeProposal?.source_email && (
                      <div className="rounded bg-emerald-500/10 p-2.5 space-y-1 border border-emerald-500/20 text-[11px]">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-emerald-700 dark:text-emerald-300">Source Email</span>
                          <Link href="/inbox">
                            <Button size="sm" variant="ghost" className="h-5 text-[10px] px-1.5 text-emerald-600 dark:text-emerald-400 hover:underline">
                              Open Original Email ➔
                            </Button>
                          </Link>
                        </div>
                        <div><span className="font-semibold">Subject:</span> "{activeProposal.source_email.subject}"</div>
                        {activeProposal.source_email.from && (
                          <div><span className="font-semibold">From:</span> {activeProposal.source_email.from.name} &lt;{activeProposal.source_email.from.email}&gt;</div>
                        )}
                      </div>
                    )}

                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      <Link href="/calendar">
                        <Button size="sm" className="bg-emerald-600 text-white hover:bg-emerald-700 font-semibold text-xs gap-1.5">
                          View & Manage in Calendar Page (/calendar) <ChevronRight className="h-3.5 w-3.5" />
                        </Button>
                      </Link>
                      <Link href="/inbox">
                        <Button size="sm" variant="outline" className="border-emerald-500/40 text-emerald-600 dark:text-emerald-400 font-semibold text-xs gap-1.5">
                          <Mail className="h-3.5 w-3.5" /> View Original Email
                        </Button>
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="mt-3 flex gap-2">
            <Input
              placeholder="Type a command e.g. 'draft reply to Devfolio' or 'give me last 4 hour email'"
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

      {/* Right Sidebar — Dynamic Command Results & Active Draft / Proposal Side Windows */}
      <div className="space-y-4">
        {/* DEDICATED AI CALENDAR PROPOSAL SIDE WINDOW CARD */}
        {activeProposal && (
          <Card className="p-4 border-emerald-500/60 bg-card shadow-xl space-y-3">
            <div className="flex items-center justify-between border-b pb-2">
              <div className="flex items-center gap-2">
                <CalendarIcon className="h-4 w-4 text-emerald-500" />
                <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">
                  AI Calendar Proposal Window
                </span>
              </div>
              <Badge variant="outline" className="text-[10px] border-emerald-500/50 text-emerald-600 dark:text-emerald-400">
                Awaiting Approval
              </Badge>
            </div>

            {(activeProposal.source_email?.subject || activeProposal.target_email?.subject) && (
              <div className="rounded-md bg-emerald-500/15 border border-emerald-500/30 p-3 text-emerald-800 dark:text-emerald-200 font-sans space-y-1.5 shadow-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-bold text-[11px] uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                    <Mail className="h-3.5 w-3.5 shrink-0 text-emerald-500" />
                    <span>SOURCE EMAIL DETAILS</span>
                  </div>
                  <Link href="/inbox">
                    <Button size="sm" variant="ghost" className="h-5 text-[10px] px-2 text-emerald-600 dark:text-emerald-300 hover:underline font-medium">
                      Open Original Email ➔
                    </Button>
                  </Link>
                </div>
                <div className="font-bold text-[12px]">
                  Subject: "{activeProposal.source_email?.subject || activeProposal.target_email?.subject}"
                </div>
                {(activeProposal.source_email?.from?.email || activeProposal.target_email?.sender) && (
                  <div className="text-[11px] opacity-90">
                    <span className="font-semibold">From / Sender:</span> {activeProposal.source_email?.from?.name || activeProposal.target_email?.sender}{" "}
                    {activeProposal.source_email?.from?.email && activeProposal.source_email.from.email !== activeProposal.source_email.from.name ? `<${activeProposal.source_email.from.email}>` : ""}
                  </div>
                )}
                {activeProposal.attendees && activeProposal.attendees.length > 0 && (
                  <div className="text-[11px] opacity-90 truncate">
                    <span className="font-semibold">To / Receiver:</span> {activeProposal.attendees.join(", ")}
                  </div>
                )}
                {activeProposal.source_email?.summary && (
                  <div className="text-[10px] opacity-85 italic line-clamp-3 pt-1 border-t border-emerald-500/20">
                    <span className="font-semibold not-italic">Email Brief:</span> "{activeProposal.source_email.summary}"
                  </div>
                )}
              </div>
            )}

            <div className="space-y-1.5 text-xs">
              <div>
                <span className="font-semibold text-muted-foreground">Title:</span>{" "}
                <span className="font-medium text-foreground">{activeProposal.title}</span>
              </div>
              <div>
                <span className="font-semibold text-muted-foreground">Proposed Slot:</span>{" "}
                <span className="font-medium text-foreground">
                  {new Date(activeProposal.start).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })} –{" "}
                  {new Date(activeProposal.end).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
              <div>
                <span className="font-semibold text-muted-foreground">Attendees:</span>{" "}
                <span className="font-medium text-foreground">
                  {activeProposal.attendees && activeProposal.attendees.length > 0 ? activeProposal.attendees.join(", ") : "None"}
                </span>
              </div>
              {activeProposal.meet_link && (
                <div className="flex items-center gap-1.5 pt-1 text-emerald-600 dark:text-emerald-400 font-medium">
                  <Video className="h-3.5 w-3.5 shrink-0" />
                  <span>Google Meet Video Link:</span>
                  <a
                    href={activeProposal.meet_link}
                    target="_blank"
                    rel="noreferrer"
                    className="underline hover:text-emerald-500 font-mono text-[11px] truncate max-w-[180px]"
                  >
                    {activeProposal.meet_link}
                  </a>
                </div>
              )}
            </div>

            {/* DOUBLE-BOOKING WARNING BANNER */}
            {activeProposal.double_booking_warnings && activeProposal.double_booking_warnings.length > 0 && (
              <div className="rounded-md border border-amber-500/40 bg-amber-500/10 p-2.5 text-xs text-amber-700 dark:text-amber-300 space-y-1">
                <div className="flex items-center gap-1.5 font-semibold">
                  <AlertTriangle className="h-4 w-4 text-amber-500" />
                  <span>Double-Booking Warning</span>
                </div>
                <p className="text-[11px] opacity-90">
                  {activeProposal.double_booking_warnings.length} pending proposal(s) overlap with this candidate time window!
                </p>
              </div>
            )}

            {/* ACTION BAR */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <Button
                size="sm"
                className="bg-emerald-600 text-white hover:bg-emerald-700 text-xs font-semibold gap-1.5 flex-1"
                onClick={() => handleInstantConfirmCalendarEvent(activeProposal.preview_id, activeProposal.approval_id)}
              >
                <CheckCircle2 className="h-3.5 w-3.5" /> Approve & Create Event
              </Button>

              <Link href="/calendar">
                <Button size="sm" variant="outline" className="text-xs gap-1 border-emerald-500/40 text-emerald-600 dark:text-emerald-400">
                  <CalendarIcon className="h-3.5 w-3.5" /> /calendar <ChevronRight className="h-3 w-3" />
                </Button>
              </Link>

              <Button
                size="sm"
                variant="ghost"
                className="text-xs text-muted-foreground hover:text-destructive p-2"
                onClick={() => setActiveProposal(null)}
                title="Close Side Window"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </div>
          </Card>
        )}
        {/* DEDICATED AI DRAFT SIDE WINDOW CARD */}
        {activeDraft && (
          <Card className="p-4 border-primary/60 bg-card shadow-xl space-y-3">
            <div className="flex items-center justify-between border-b pb-2">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" />
                <span className="text-xs font-semibold text-primary uppercase tracking-wider">
                  AI Reply Draft Window
                </span>
              </div>
              <Badge variant="outline" className="text-[10px] border-amber-500/50 text-amber-600 dark:text-amber-400">
                Awaiting Approval
              </Badge>
            </div>

            <div className="space-y-1 text-xs">
              <div>
                <span className="font-semibold text-muted-foreground">To:</span>{" "}
                <span className="font-medium text-foreground">{activeDraft.recipient || "Recipient"}</span>
              </div>
              <div>
                <span className="font-semibold text-muted-foreground">Subject:</span>{" "}
                <span className="font-medium text-foreground">{activeDraft.subject || "Reply Draft"}</span>
              </div>
            </div>

            {/* GAP DETECTION WARNING BANNER */}
            {activeDraft.has_gaps && (
              <div className="rounded-md border border-amber-500/40 bg-amber-500/10 p-2.5 text-xs text-amber-700 dark:text-amber-300 space-y-1">
                <div className="flex items-center gap-1.5 font-semibold">
                  <AlertTriangle className="h-4 w-4 text-amber-500" />
                  <span>Knowledge Base Gap Flagged</span>
                </div>
                {activeDraft.gap_notes && activeDraft.gap_notes.length > 0 ? (
                  <ul className="list-disc list-inside text-[11px] space-y-0.5 opacity-90">
                    {activeDraft.gap_notes.map((g, idx) => (
                      <li key={idx}>{g}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-[11px] opacity-90">Missing unverified facts flagged in draft text.</p>
                )}
              </div>
            )}

            {/* DRAFT BODY PREVIEW WINDOW */}
            <div className="rounded-lg border bg-muted/40 p-3 text-xs font-sans whitespace-pre-wrap max-h-48 overflow-y-auto leading-relaxed border-border/80">
              {activeDraft.draft_body}
            </div>

            {/* ACTION BAR */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <Button
                size="sm"
                className="bg-primary text-primary-foreground hover:bg-primary/90 text-xs font-semibold gap-1.5 flex-1"
                onClick={() => handleInstantApproveAndSend(activeDraft.draft_id, activeDraft.draft_body)}
              >
                <CheckCircle2 className="h-3.5 w-3.5" /> Approve & Send Now
              </Button>

              <Link href="/replies">
                <Button size="sm" variant="outline" className="text-xs gap-1">
                  <FileText className="h-3.5 w-3.5" /> /replies
                </Button>
              </Link>

              <Button
                size="sm"
                variant="ghost"
                className="text-xs text-muted-foreground hover:text-destructive p-2"
                onClick={() => setActiveDraft(null)}
                title="Close Side Window"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </div>
          </Card>
        )}

        {/* SEARCH / QUERY RESULTS SIDEBAR PANEL */}
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
          !activeDraft && (
            <>
              <Card className="p-4">
                <div className="text-xs font-medium text-muted-foreground">COMMAND RESULTS PANEL</div>
                <p className="mt-2 text-xs text-muted-foreground">
                  When you issue an email query command or request a reply draft, the results and interactive AI draft card will render right here in this side window!
                </p>
              </Card>

              <Card className="p-4">
                <div className="text-xs font-medium text-muted-foreground">TRY THESE COMMANDS</div>
                <div className="mt-3 flex flex-col gap-1.5 text-sm">
                  {[
                    "draft reply to Devfolio inquiry",
                    "give me last 4 hour email",
                    "show emails from Google",
                    "give me 10 emails",
                    "find emails about Microsoft",
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
          )
        )}
      </div>
    </div>
  );
}
