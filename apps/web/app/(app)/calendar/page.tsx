"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Calendar as CalendarIcon,
  Clock,
  ShieldCheck,
  Users,
  Video,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Loader2,
} from "lucide-react";

interface MeetingRecord {
  id: string;
  status: "previewed" | "confirmed" | "cancelled";
  calendar_event_id?: string;
  participants: Array<{ email?: string; displayName?: string }>;
  proposed_slots: Array<{ start: string; end: string; title?: string }>;
  created_at: string;
}

interface FreeSlot {
  start: string;
  end: string;
  duration_minutes: number;
  timezone_display?: Record<string, string>;
}

export default function CalendarPage() {
  const { getToken } = useAuth();
  const [meetings, setMeetings] = useState<MeetingRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [naturalInput, setNaturalInput] = useState<string>("");
  const [extracting, setExtracting] = useState<boolean>(false);
  
  // Extraction & Availability State
  const [extractedTitle, setExtractedTitle] = useState<string>("");
  const [extractedDuration, setExtractedDuration] = useState<number>(60);
  const [extractedParticipants, setExtractedParticipants] = useState<string>("");
  const [extractedDescription, setExtractedDescription] = useState<string>("");
  const [freeSlots, setFreeSlots] = useState<FreeSlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<FreeSlot | null>(null);
  const [doubleBookWarnings, setDoubleBookWarnings] = useState<any[]>([]);
  const [addMeet, setAddMeet] = useState<boolean>(true);

  // Active Preview State
  const [activePreview, setActivePreview] = useState<any | null>(null);
  const [previewing, setPreviewing] = useState<boolean>(false);
  const [confirming, setConfirming] = useState<boolean>(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const getHeaders = async () => {
    const token = await getToken();
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  };

  const fetchMeetings = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = await getHeaders();
      const res = await fetch(`${apiUrl}/calendar/meetings`, { headers });
      if (res.ok) {
        const data = await res.json();
        setMeetings(data);
      }
    } catch (err) {
      console.error("Failed to fetch meetings:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMeetings();
  }, []);

  const handleExtractAndCheckAvailability = async () => {
    if (!naturalInput.trim()) return;
    setExtracting(true);
    setActionError(null);
    setActionSuccess(null);
    setActivePreview(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = await getHeaders();

      // 1. Extract Details
      const extractRes = await fetch(`${apiUrl}/calendar/extract`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          text: naturalInput,
          user_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
        }),
      });

      if (!extractRes.ok) throw new Error("Failed to parse meeting details");
      const details = await extractRes.json();

      setExtractedTitle(details.title || "Sync Meeting");
      setExtractedDuration(details.duration_minutes || 60);
      setExtractedParticipants((details.participants || []).join(", "));
      setExtractedDescription(details.description || "");

      // 2. Check Availability
      const availRes = await fetch(`${apiUrl}/calendar/availability`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          preferred_date: details.date,
          preferred_time: details.time,
          duration_minutes: details.duration_minutes || 60,
          participants: details.participants || [],
          user_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
        }),
      });

      if (availRes.ok) {
        const availData = await availRes.json();
        setFreeSlots(availData.free_slots || []);
        setDoubleBookWarnings(availData.double_booking_warnings || []);
        if (availData.free_slots && availData.free_slots.length > 0) {
          setSelectedSlot(availData.free_slots[0]);
        }
      }
    } catch (err: any) {
      setActionError(err.message || "Failed to process scheduling request");
    } finally {
      setExtracting(false);
    }
  };

  const handleGeneratePreview = async () => {
    if (!selectedSlot) return;
    setPreviewing(true);
    setActionError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = await getHeaders();

      const participantsList = extractedParticipants
        .split(",")
        .map((p) => p.trim())
        .filter((p) => p.length > 0);

      const res = await fetch(`${apiUrl}/calendar/preview`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          title: extractedTitle,
          start_time: selectedSlot.start,
          end_time: selectedSlot.end,
          duration_minutes: extractedDuration,
          participants: participantsList,
          description: extractedDescription,
          generate_meet: addMeet,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to create preview");
      }

      const previewData = await res.json();
      setActivePreview(previewData);
      setActionSuccess("Meeting proposal created! Review and confirm below.");
      fetchMeetings();
    } catch (err: any) {
      setActionError(err.message || "Preview failed");
    } finally {
      setPreviewing(false);
    }
  };

  const handleConfirmEvent = async () => {
    if (!activePreview) return;
    setConfirming(true);
    setActionError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = await getHeaders();

      const res = await fetch(`${apiUrl}/calendar/confirm`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          approval_id: activePreview.approval_id,
          preview_id: activePreview.preview_id,
          event_body: activePreview.event_body,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to confirm event");
      }

      const confirmData = await res.json();
      setActionSuccess(`Calendar event confirmed! ${confirmData.hangout_link ? `Meet Link: ${confirmData.hangout_link}` : ""}`);
      setActivePreview(null);
      fetchMeetings();
    } catch (err: any) {
      setActionError(err.message || "Confirmation failed");
    } finally {
      setConfirming(false);
    }
  };

  const pendingCount = meetings.filter((m) => m.status === "previewed").length;
  const confirmedCount = meetings.filter((m) => m.status === "confirmed").length;

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Calendar Agent</h1>
        <p className="text-sm text-muted-foreground">
          Extract scheduling intent, compute ranked candidate slots across timezones, and confirm with Google Meet links.
        </p>
      </div>

      {/* Stats Header */}
      <div className="grid gap-3 md:grid-cols-3">
        <Card className="p-4">
          <div className="text-xs text-muted-foreground">Total Proposals</div>
          <div className="mt-2 text-2xl font-semibold">{meetings.length}</div>
        </Card>
        <Card className="p-4">
          <div className="text-xs text-muted-foreground">Pending Approval</div>
          <div className="mt-2 text-2xl font-semibold text-amber-500">{pendingCount}</div>
        </Card>
        <Card className="p-4">
          <div className="text-xs text-muted-foreground">Confirmed Events</div>
          <div className="mt-2 text-2xl font-semibold text-emerald-500">{confirmedCount}</div>
        </Card>
      </div>

      {/* Natural Language Assistant */}
      <Card className="p-5 space-y-4 border-primary/20 bg-primary/5">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          <h2 className="font-semibold text-base">Natural Language Scheduling Assistant</h2>
        </div>
        <div className="flex gap-2">
          <Input
            placeholder="e.g., Schedule a 45 min project review with alex@example.com for tomorrow afternoon"
            value={naturalInput}
            onChange={(e) => setNaturalInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleExtractAndCheckAvailability()}
          />
          <Button onClick={handleExtractAndCheckAvailability} disabled={extracting || !naturalInput.trim()}>
            {extracting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
            Find Free Slots
          </Button>
        </div>

        {/* Double Booking Warnings */}
        {doubleBookWarnings.length > 0 && (
          <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-md text-xs text-amber-600 dark:text-amber-400 flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
            <div>
              <span className="font-semibold">Double-Booking Warning:</span> You have {doubleBookWarnings.length} pending meeting proposal(s) overlapping with these candidate search windows.
            </div>
          </div>
        )}

        {/* Extracted Details & Free Slots Selection */}
        {selectedSlot && (
          <div className="space-y-4 pt-3 border-t border-border">
            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Meeting Title</label>
                <Input value={extractedTitle} onChange={(e) => setExtractedTitle(e.target.value)} className="mt-1" />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Participants (comma separated)</label>
                <Input value={extractedParticipants} onChange={(e) => setExtractedParticipants(e.target.value)} className="mt-1" />
              </div>
            </div>

            {/* Ranked Candidate Free Slots */}
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-2">Ranked Candidate Free Slots</label>
              <div className="grid gap-2 md:grid-cols-2">
                {freeSlots.map((slot, idx) => {
                  const isSelected = selectedSlot.start === slot.start;
                  return (
                    <div
                      key={idx}
                      onClick={() => setSelectedSlot(slot)}
                      className={`p-3 rounded-lg border cursor-pointer text-xs transition-all ${
                        isSelected
                          ? "border-primary bg-primary/10 font-medium"
                          : "border-border hover:border-primary/50"
                      }`}
                    >
                      <div className="flex justify-between items-center">
                        <span className="font-medium">Option #{idx + 1}</span>
                        <Badge variant={isSelected ? "default" : "outline"} className="text-[10px]">
                          {slot.duration_minutes} min
                        </Badge>
                      </div>
                      <div className="mt-1 font-mono text-[11px]">
                        {new Date(slot.start).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })}
                      </div>
                      {slot.timezone_display && (
                        <div className="mt-1 text-[10px] text-muted-foreground">
                          {Object.entries(slot.timezone_display).map(([tz, val]) => (
                            <div key={tz}>{val}</div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Meet link option & Action */}
            <div className="flex items-center justify-between pt-2">
              <label className="flex items-center gap-2 text-xs font-medium cursor-pointer">
                <input type="checkbox" checked={addMeet} onChange={(e) => setAddMeet(e.target.checked)} className="rounded" />
                <Video className="h-4 w-4 text-emerald-500" />
                Generate Google Meet Video Conference Link
              </label>
              <Button onClick={handleGeneratePreview} disabled={previewing}>
                {previewing ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Generate Proposal Preview
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Action Messages */}
      {actionSuccess && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-md text-sm text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4" />
          {actionSuccess}
        </div>
      )}
      {actionError && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-md text-sm text-rose-600 dark:text-rose-400 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          {actionError}
        </div>
      )}

      {/* Active Proposal Preview Card */}
      {activePreview && (
        <Card className="p-5 border-amber-500/40 bg-amber-500/5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-amber-500" />
              <h3 className="font-semibold">Meeting Proposal Awaiting Approval</h3>
            </div>
            <Badge variant="outline" className="border-amber-500 text-amber-500">
              Approval ID: {activePreview.approval_id?.slice(0, 8)}...
            </Badge>
          </div>

          <div className="text-sm space-y-1">
            <div><span className="font-medium text-muted-foreground">Title:</span> {activePreview.title}</div>
            <div>
              <span className="font-medium text-muted-foreground">Time:</span>{" "}
              {new Date(activePreview.start).toLocaleString()} – {new Date(activePreview.end).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </div>
            <div><span className="font-medium text-muted-foreground">Attendees:</span> {(activePreview.attendees || []).join(", ") || "None"}</div>
            {activePreview.conference_data && (
              <div className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-medium text-xs pt-1">
                <Video className="h-3.5 w-3.5" /> Google Meet Video Conference Included
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button size="sm" variant="ghost" onClick={() => setActivePreview(null)}>
              Discard
            </Button>
            <Button size="sm" onClick={handleConfirmEvent} disabled={confirming}>
              {confirming ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Approve & Create Calendar Event
            </Button>
          </div>
        </Card>
      )}

      {/* Existing Meeting Proposals */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Your Meeting Proposals</h2>
        {loading ? (
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : meetings.length === 0 ? (
          <Card className="p-8 text-center text-muted-foreground text-sm">
            No meeting proposals found. Use the assistant above to schedule a meeting!
          </Card>
        ) : (
          meetings.map((m) => {
            const slot = m.proposed_slots && m.proposed_slots.length > 0 ? m.proposed_slots[0] : null;
            return (
              <Card key={m.id} className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <CalendarIcon className="h-4 w-4 text-primary" />
                      <span className="font-medium">{slot?.title || "Meeting Proposal"}</span>
                      {m.status === "previewed" ? (
                        <Badge variant="outline" className="border-amber-500/40 text-amber-500">
                          <ShieldCheck className="mr-1 h-3 w-3" /> Awaiting Approval
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-500">
                          Confirmed
                        </Badge>
                      )}
                    </div>
                    {slot && (
                      <div className="mt-2 flex flex-wrap gap-4 text-xs text-muted-foreground">
                        <span className="inline-flex items-center gap-1">
                          <Clock className="h-3 w-3" /> {new Date(slot.start).toLocaleString()}
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <Users className="h-3 w-3" /> {m.participants.map((p) => p.email || p.displayName).join(", ")}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}
