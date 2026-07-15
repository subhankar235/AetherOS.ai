═══════════════════════════════════════════════════════════
 PATH A — AUTOMATIC (silent, no AI "action", no user command)
═══════════════════════════════════════════════════════════

New email arrives
      ↓
Gmail Pub/Sub webhook fires
      ↓
Inbox Agent (auto_pipeline)
      ↓
Summarize + Categorize + Label + Priority + Urgency
      ↓
Save to DB
      ↓
WebSocket push → Dashboard updates live

  ⛔ STOPS HERE — no reply, no schedule, no payment, ever automatic


═══════════════════════════════════════════════════════════
 PATH B — COMMAND-DRIVEN (voice or text, user-initiated)
═══════════════════════════════════════════════════════════

User opens Command Center (avatar UI)
      ↓
Speaks or types a command
      │
      ├─ Voice → STT (ElevenLabs) → text
      └─ Text → used directly
      ↓
Supervisor Agent (always running)
      ↓
Intent Router → figures out WHAT the user wants
      ↓
Context Manager → resolves "it" / "the first one" / "that meeting"
      ↓
Routes to ONE specialized agent (spins up on demand)

      ┌───────────────┬───────────────┬───────────────┬───────────────┬───────────────┐
      ▼               ▼               ▼               ▼               ▼
  Inbox Agent     Reply Agent    Calendar Agent   Knowledge Agent  Research Agent   Payment Agent
  (search/read)   (draft reply)  (schedule mtg)   (RAG answer)     (company report) (invoice pay)
      │               │               │               │               │               │
      │          Draft shown      Preview shown        │          Report shown    Preview shown
      │               │               │                │               │               │
      │          User edits      User picks slot        │               │          User reviews
      │          ("shorten")     or edits time           │               │          (fraud/policy
      │               │               │                │               │           check shown)
      │               ▼               ▼                │               │               ▼
      │          ⏸ APPROVAL GATE  ⏸ APPROVAL GATE         │               │          ⏸ APPROVAL GATE
      │          "Send it?"       "Confirm?"               │               │          "Approve payment?"
      │               │               │                │               │               │
      │          User approves   User approves            │               │          User approves
      │               ▼               ▼                │               │               ▼
      │          Gmail API      Calendar API              │               │          Payment API
      │          sends email    creates event              │               │          executes pay
      ▼               ▼               ▼               ▼               ▼               ▼
   Raw structured result returned to Supervisor
   (e.g., {5 new emails, 2 high priority} / {draft ready} / {event created})
      ↓
   ┌─────────────────────────────────────────────────────────────┐
   │  🎙 HUMAN VOICE LAYER (only runs if input mode = voice)      │
   │                                                               │
   │  1. Conversational rewrite (GPT-5.5)                          │
   │     structured data → natural spoken sentence                 │
   │     ❌ "Query returned 5 results, 2 high priority."           │
   │     ✅ "You've got 5 new emails — 2 look important,           │
   │         want me to read those first?"                         │
   │                                                                │
   │  2. Tone adaptation based on context                          │
   │     - Daily triage        → casual, warm                      │
   │     - Approval requests   → careful, neutral, clear            │
   │     - Fraud/suspicious    → calm, serious                     │
   │                                                                │
   │  3. ElevenLabs TTS (natural/expressive voice, not robotic)     │
   │                                                                │
   │  4. Avatar animates in sync with audio                         │
   │     (idle → listening → thinking → SPEAKING w/ mouth/pulse)    │
   │     — feels like a person responding, not a machine reading    │
   └─────────────────────────────────────────────────────────────┘
      ↓
   Result shown as text in Command Center (always)
   + spoken aloud via humanized voice (if voice mode)
      ↓
   Agent TERMINATES (only Supervisor stays alive)
      ↓
   Audit log written for any consequential action
      ↓
   Supervisor waits for next command


═══════════════════════════════════════════════════════════
 GOLDEN RULES
═══════════════════════════════════════════════════════════
1. Detection / drafting / preview  → agent can do this automatically once triggered by command
2. Sending / scheduling / paying   → ALWAYS blocked behind Approval Gate — no exceptions
3. Voice responses are NEVER raw data read aloud — always passed through the
   conversational rewrite + tone adaptation layer first, so it sounds like
   a person talking to you, not a generic assistant reciting output
