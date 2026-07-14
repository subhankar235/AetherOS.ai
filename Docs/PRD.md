# Product Requirements Document (PRD)
# AI Email Assistant

**Document Owner:** Product & Engineering Leadership
**Version:** 1.0
**Status:** Draft for Engineering Kickoff
**Classification:** Internal — Founding Team & Early Engineering Hires

---

## Table of Contents

1. Vision
2. Problem Statement
3. Goals
4. User Personas
5. Functional Requirements
6. Non-Functional Requirements
7. User Flows
8. AI Workflows
9. Agent Architecture
10. API Integrations
11. Database Design
12. Folder Structure
13. Security
14. Deployment
15. Future Roadmap
16. Risks
17. Success Metrics

---

## 1. Vision

Email is the operating system of modern work, but it has become a liability instead of a productivity tool. Knowledge workers spend 2–3 hours a day triaging, reading, and replying to email — most of it low-value, repetitive, or context-switching work that a well-designed AI system can absorb.

**The AI Email Assistant's vision is to become the autonomous "chief of staff" for a person's inbox** — an assistant that:

- Watches the inbox continuously and silently, doing only the minimum automatic work needed to keep the user informed (fetch, summarize, prioritize, categorize).
- Never acts on the user's behalf without being asked. Every consequential action (sending a reply, scheduling a meeting, paying an invoice) is user-initiated and, where money or external commitments are involved, user-approved.
- Understands company-specific context (policies, tone, product knowledge) so its replies sound like the user, not like a generic chatbot.
- Is operated conversationally — by voice or text — the same way a founder would delegate to a real executive assistant: *"Show me what came in from investors this week," "Reply and make it warmer," "Schedule this for Thursday."*
- Starts as an email assistant, but is architected from day one as a general-purpose, agentic **work assistant**, with Payments, CRM, and multi-channel (Slack, Teams, Outlook) support on the roadmap.

The long-term bet: the inbox is the highest-frequency, highest-context surface in a knowledge worker's day, and whoever owns a trustworthy, controllable AI layer on top of it owns the entry point to broader workplace automation.

---

## 2. Problem Statement

### 2.1 The problem today

- **Volume without triage.** The average professional receives 100–150 emails/day. Existing inboxes (Gmail, Outlook) sort by time, not importance, forcing manual triage every single day.
- **Context is scattered.** Answering a customer or investor properly requires cross-referencing company docs, past threads, and policies — information that lives outside the inbox.
- **Existing "AI email" tools overreach or underdeliver.** Many auto-send tools create trust and compliance problems (an AI that emails on your behalf without approval is a liability). Others are just "smart compose" — they don't understand company context or coordinate multi-step actions (read → reply → schedule → follow up).
- **Fragmented tooling.** Scheduling happens in Calendar, knowledge lives in Notion/Docs, research happens in a browser, invoices get paid in a separate finance tool. None of these are connected to the place where the *request* actually originates: the inbox.
- **Voice-first, hands-free workflows are absent.** Founders, executives, and sales reps want to manage email while driving, walking, or multitasking — this is essentially unsupported today.

### 2.2 Why now

- LLMs (GPT-5.5-class models) are now reliable enough for multi-step tool use and long-context reasoning over threads and documents.
- Multi-agent orchestration frameworks (LangGraph) make it practical to build supervisor/sub-agent systems with clean lifecycle boundaries instead of one monolithic prompt.
- RAG infrastructure (vector DBs, embeddings) is mature and cheap enough to give every user/company a private, semantically searchable knowledge base.
- Voice AI (ElevenLabs-class STT/TTS) has crossed the threshold of natural, low-latency conversational quality, making voice a viable primary interface rather than a gimmick.

### 2.3 Core design constraint that differentiates us

Most competitors either automate too much (risk, trust, compliance issues) or automate too little (just a smarter autocomplete). Our differentiator is a **strict automation boundary**:

> Only four things ever happen automatically: fetching new email, generating a summary, assigning a priority, and assigning a category. Everything else — search, reading, replying, scheduling, research, payments — happens only in direct response to an explicit user command, and any action with external or financial consequence requires explicit user approval before execution.

This is a product principle, not just an engineering detail — it is core to user trust and is repeated throughout this document as an architecture rule.

---

## 3. Goals

### 3.1 Product Goals

| Goal | Description |
|---|---|
| G1 — Reduce triage time | Cut time spent scanning/prioritizing inbox by 70% via automatic summarization and priority scoring. |
| G2 — Trustworthy automation | Zero unapproved sends, zero unapproved calendar invites, zero unapproved payments — 100% of consequential actions gated by explicit user approval. |
| G3 — Context-aware replies | Replies should require minimal editing (target: <20% edit distance) because the Reply Agent grounds itself in company knowledge and thread history. |
| G4 — Voice-first control | Every core workflow (search, read, reply, schedule) achievable by voice, not just text. |
| G5 — Modular agent platform | Ship an agent architecture that lets us add Payment Agent, Slack/Teams/Outlook, and CRM integrations without re-architecting the Supervisor. |

### 3.2 Business Goals

- Validate willingness to pay with a usage-based/seat-based SaaS model (founders, sales teams, executive assistants, small business owners as early ICP).
- Land-and-expand: start with individual power users (Gmail + Calendar), expand into team/workspace tier with shared Company Memory and Playbooks.
- Build a defensible data moat via the Company Memory / Knowledge Base — the more a company uses it, the better and more differentiated the replies become, increasing switching cost.

### 3.3 Non-Goals (for v1)

- We are **not** building a full email client replacement (no custom SMTP/IMAP, no offline mode) — v1 relies entirely on the Gmail API.
- We are **not** auto-sending or auto-scheduling anything without explicit approval, even for "obviously safe" cases.
- We are **not** shipping the Payment Agent in MVP — it is explicitly scoped as Future (Section 15), included in architecture design but not implemented.
- We are **not** supporting non-Google providers (Outlook, IMAP) at launch.

---

## 4. User Personas

### 4.1 Persona A — "Priya," the Startup Founder
- Manages investor updates, customer emails, hiring, and partnerships alone.
- Receives 150+ emails/day, is usually mobile or in back-to-back meetings.
- Primary need: rapid triage ("what actually needs me today?"), fast voice-driven replies between meetings, meeting scheduling without leaving the flow of a conversation.
- Success = she never has to open Gmail directly; the AI Command Center is her inbox.

### 4.2 Persona B — "Daniel," the Account Executive
- High email volume with prospects and customers; timing and tone matter a lot.
- Needs: reply drafts that reflect the sales playbook and product pricing correctly, fast scheduling of demo calls with Meet links, follow-up detection.
- Success = shorter sales cycle, fewer missed follow-ups, consistent brand voice across reps.

### 4.3 Persona C — "Meera," the Executive Assistant
- Manages inboxes on behalf of 1–2 executives.
- Needs: VIP contact prioritization, delegated approval workflows, ability to prep drafts for the executive to approve quickly, meeting coordination across multiple calendars.
- Success = she can process an executive's inbox in a fraction of the time, with full auditability of what the AI drafted vs. what was actually sent.

### 4.4 Persona D — "Alex," the Small Business Owner
- Handles support tickets, vendor invoices, and supplier communication personally.
- Needs: knowledge-base-grounded replies to repeat customer questions (refund policy, shipping), and — in the future — semi-automated invoice payment with strict policy checks.
- Success = fewer hours on admin, invoices tracked and paid on time without manual data entry.

### 4.5 Persona E (secondary) — "IT/Security Admin"
- Not a daily user, but a gatekeeper for enterprise rollout.
- Needs: OAuth scoping control, audit logs, role-based access, data residency and retention policy clarity.
- Success = confidence to approve the tool for company-wide use.

---

## 5. Functional Requirements

Each feature below includes: description, actors, trigger, detailed behavior, and edge cases.

### 5.1 AI Command Center (Primary Interface) ⭐

**Description:** A single input surface (voice or text) through which the user issues every non-automatic instruction to the system. This is the "front door" — users never talk to a specific agent; they talk to the Supervisor Agent, which decides what to do.

**Trigger:** User types or speaks a command.

**Behavior:**
1. Input captured as text (typed) or transcribed (voice, via ElevenLabs STT).
2. Supervisor Agent performs intent classification against the known task catalog (search, read, reply, schedule, knowledge query, research, payment [future], help).
3. Supervisor extracts entities relevant to that intent (time ranges, sender names, email indices like "the second one," meeting particulars).
4. Supervisor resolves references using conversation context (Section 8.5 — coreference resolution), e.g., "reply to it" refers to the last-viewed email.
5. Supervisor invokes exactly one specialized agent per discrete task (see Section 9 for orchestration rules on multi-step commands).
6. Agent performs its task and returns a structured result to the Supervisor, which renders it to the UI (and, in voice mode, converts a natural-language summary to speech via TTS).
7. Agent terminates. Supervisor remains active, retaining context for the next command.

**Edge Cases:**
- **Ambiguous intent** ("do something with this email") → Supervisor asks a clarifying question rather than guessing at a consequential action.
- **Multi-intent command** ("reply and then schedule a meeting") → Supervisor decomposes into an ordered task queue and invokes agents sequentially, carrying output of step N into step N+1.
- **No active context** ("reply to it" with nothing previously opened) → Supervisor responds asking which email.
- **Command referencing a stale/deleted email** (e.g., user archived it via Gmail directly, outside the app) → Inbox Agent re-fetches and Supervisor informs the user if the email no longer exists.
- **Voice transcription error** (e.g., "Sundar" transcribed as "Sander") → Supervisor performs fuzzy contact matching and, on low confidence, confirms with the user before searching.

---

### 5.2 AI Inbox (Automatic Background Processing)

**Description:** The only fully automatic feature set. The moment a new email arrives, the Inbox Agent processes it without any user command.

**Trigger:** New email detected via Gmail push notification (Pub/Sub) or polling fallback.

**Behavior (strict scope — see Architecture Rules):**
1. Fetch the new email via Gmail API.
2. Run LLM analysis to generate:
   - Short summary (1–2 sentences)
   - Priority: High / Medium / Low
   - Category (e.g., Sales, Support, Internal, Newsletter, Personal, Finance)
   - Urgency flag
   - Reply-required flag (Yes/No)
3. Persist metadata to PostgreSQL.
4. Push update to the dashboard via WebSocket (so the inbox list updates live without a refresh).

**Explicitly out of scope for automatic processing:** no reply is drafted, no meeting is created, no payment is initiated, no email is archived/labeled/deleted automatically. The system **waits**.

**Edge Cases:**
- **Burst arrival** (50 emails after being offline) → processed via a queued background job (Celery + Redis) rather than serially blocking, with priority given to the most recent items first.
- **Non-English emails** → summary/category still generated; language detected and stored as metadata; summary generated in the user's preferred language (configurable) with the option to view the original.
- **Malformed / spoofed / phishing-like emails** → Inbox Agent flags a "Suspicious" category in addition to normal categorization; content is still summarized but the AI does not treat any embedded instructions in the email body as commands (see Section 13.5 — prompt injection defense).
- **Attachments-only emails with no body text** → summary generated from attachment filename/type and subject line, with an explicit note "no email body content."
- **Duplicate/thread updates** (reply to an existing thread) → treated as a thread update, not a new top-level item; summary reflects "what's new in this thread."

---

### 5.3 AI Dashboard

**Description:** The home view summarizing inbox state at a glance.

**Contents:** new email count, high-priority count, unread count, meeting requests detected, pending replies, follow-up reminders, AI-recommended next actions.

**Behavior:** Reactively updated — DB changes flow through Redis pub/sub → WebSocket → dashboard re-render, so the founder persona ("Priya") never needs to manually refresh.

**Edge Cases:**
- Multiple browser tabs/devices open → WebSocket broadcasts to all active sessions for that user; state stays consistent.
- Large inbox history on first login → dashboard shows only a bounded recent window (e.g., last 7 days) while historical backfill processes asynchronously, with a progress indicator.

---

### 5.4 Voice Assistant

**Description:** Full voice-driven control of the Command Center, using ElevenLabs for STT and TTS.

**Behavior:**
1. User taps microphone (or uses wake-word/hold-to-talk pattern) and speaks.
2. Audio streamed to ElevenLabs STT → transcript returned.
3. Transcript handled exactly like a typed command by the Supervisor Agent.
4. Response rendered as text in the UI **and** spoken back via ElevenLabs TTS, summarizing the result conversationally (e.g., "You have 3 new high-priority emails, want me to read them?").

**Edge Cases:**
- **Noisy environment / low transcription confidence** → system asks the user to repeat rather than acting on a low-confidence guess for consequential commands (reply/send/schedule/pay).
- **Long dictated replies** (user dictates full email body) → streamed transcription with a visible live draft so the user can interrupt/correct before submission.
- **Privacy** — voice audio is not persisted after transcription unless the user has explicitly opted into "voice history" for QA purposes.

---

### 5.5 Natural Language Search

**Description:** Converts plain-English queries into structured Gmail search queries.

**Examples supported:** by sender, by date/time range, by keyword, by category, unread-only, attachments-only, meeting-requests-only.

**Behavior:**
1. Supervisor routes to Inbox Agent with the raw query + parsed intent.
2. Inbox Agent (via GPT-5.5) translates natural language into Gmail's query syntax (e.g., `from:sundar after:2026/07/14`).
3. Query executed against Gmail API; results returned and rendered.
4. Agent terminates.

**Edge Cases:**
- **Relative time expressions** ("last six hours," "yesterday afternoon") resolved against the user's local timezone, not server time.
- **Ambiguous sender names** ("emails from Mike") with multiple contact matches → Inbox Agent returns a disambiguation prompt listing matching contacts.
- **Zero results** → friendly empty state with a suggestion to broaden the query, not a silent blank screen.
- **Overly broad queries** ("show me everything") → paginated results with a sensible default limit (e.g., 25) rather than attempting to return thousands of emails at once.

---

### 5.6 Reading an Email (Smart Email Viewer)

**Description:** Opens a specific email with full context.

**Behavior:** On command ("open the first email"), Inbox Agent retrieves full email body, thread history, and attachments; UI displays AI summary, thread summary, key action items, detected deadlines, and suggested next actions (e.g., "Reply," "Schedule meeting," "Add to knowledge base").

**Edge Cases:**
- **Very long threads** (50+ messages) → thread summary generated hierarchically (summarize in chunks, then summarize the summaries) to stay within context limits.
- **Large attachments** → preview generated for common types (PDF, images, docx); unsupported types show metadata only with a download link.
- **Index referencing ambiguity** ("open the first email" after a re-sort) → Supervisor always resolves "first/second/etc." against the currently rendered list order in the UI, not an internal/stale order.

---

### 5.7 AI Reply Assistant + Draft Editor

**Description:** Generates and iteratively refines reply drafts grounded in thread context and company knowledge; requires explicit user approval to send.

**Behavior (see full workflow in Section 8.3):**
1. Reply Agent reads the target email and full thread.
2. Requests relevant context from the Knowledge Agent (RAG over Company Memory).
3. Applies a matching Playbook if one exists for this scenario (e.g., "Interview Invitation" playbook).
4. Generates a draft; displays it; **waits**.
5. User can issue any number of edit commands: "make it more professional," "shorten it," "make it friendlier," "add a calendar link," "fix grammar," or free-form custom instructions.
6. Each edit command triggers a rewrite of the current draft (not a from-scratch regeneration) to preserve intentional edits the user already made.
7. User says "send it" → confirmation screen shown (recipient, subject, full body) → user approves → Reply Agent sends via Gmail API → Reply Agent terminates.

**Edge Cases:**
- **User manually edits the draft text box, then issues a voice command** → the manual edits are treated as the current source-of-truth draft; AI rewrites operate on that edited version, never silently reverting to a prior AI version.
- **User says "send it" without ever seeing a confirmation** (race condition / fast voice flow) → system always inserts the confirmation step; there is no voice shortcut that bypasses approval.
- **Reply requires information not present in Knowledge Base or thread** → draft explicitly flags the gap (e.g., "[I don't have our current refund window — please confirm]") rather than fabricating a policy detail.
- **User abandons mid-edit** (navigates away) → draft auto-saved so it can be resumed later without data loss.
- **Reply-all vs. reply-to-sender** ambiguity → Supervisor asks or defaults based on thread's prior reply pattern, always shown clearly on the confirmation screen.

---

### 5.8 Meeting Scheduler (Calendar Agent)

**Description:** Detects and executes meeting scheduling from natural language, grounded in real calendar availability.

**Behavior (see Section 8.4):**
1. On command ("schedule this meeting" / "schedule this for Thursday afternoon"), Calendar Agent extracts date, time, duration, and participants from the email/thread and/or the user's command.
2. Checks Google Calendar for conflicts; computes free slots if no time was explicit.
3. Generates a Google Meet link and a preview (proposed time, attendees, title, Meet link).
4. **Waits** for user confirmation.
5. On "confirm," creates the calendar event and sends invitations via Calendar API; terminates.

**Edge Cases:**
- **No free slot matches the requested window** → Calendar Agent proposes the nearest alternatives rather than failing silently.
- **Cross-timezone participants** → all proposed times shown with timezone labels for both organizer and (when known) invitee.
- **Recurring meeting requests** ("schedule this weekly") → explicit recurrence rule shown in the preview, not assumed automatically.
- **Double-booking risk** (user has two pending, unconfirmed proposals for overlapping times) → system warns before creating the second event.
- **Participant email extracted incorrectly** (e.g., CC'd support alias mistaken for a required attendee) → all detected participants are editable on the preview screen before confirmation.

---

### 5.9 Company Memory (Knowledge Base / RAG)

**Description:** Centralized repository of company documents that grounds AI replies and answers in accurate, source-specific information.

**Supported content:** handbook, SOPs, product docs, FAQs, brand guidelines, pricing, sales playbooks, HR policies, legal docs, past emails, contracts, marketing materials, internal docs, custom notes, website URLs.

**Supported file types (v1):** PDF, DOCX, TXT, Markdown, CSV.

**Behavior (see Section 8.6):**
1. Upload → parsed (Unstructured/PyMuPDF/DOCX parser) → chunked → embedded (OpenAI text-embedding-3-large) → stored in Qdrant with metadata (source, upload date, doc type, owner).
2. On any query needing grounding (Reply Agent draft, direct knowledge question), Knowledge Agent performs semantic search, retrieves top-k relevant chunks, and returns them with source citations to the calling agent.
3. Answers to direct questions ("What does our refund policy say?") are generated with inline references to which document the answer came from.

**Edge Cases:**
- **Conflicting documents** (two versions of a policy) → Knowledge Agent surfaces both with source/date metadata and flags the conflict rather than silently picking one.
- **No relevant document found** → explicit "I couldn't find this in your Company Memory" response rather than a hallucinated answer.
- **Large document sets** → incremental re-indexing on upload; users can see indexing status (queued/processing/ready) per document.
- **Sensitive documents** (legal, HR) → access-controlled at the document level so not every team member's queries can retrieve every document (see Section 13.4, RBAC).

---

### 5.10 Playbooks

**Description:** Reusable, structured reply/workflow templates (e.g., Interview Workflow, Sales Workflow, Customer Support Workflow, Complaint Handling Workflow) that the Reply Agent applies automatically when it detects a matching scenario, or that a user can explicitly invoke.

**Edge Cases:**
- **Playbook conflicts with Knowledge Base content** (e.g., outdated pricing baked into an old playbook) → Knowledge Base retrieval always takes precedence for factual content; the Playbook governs structure/tone only.
- **No matching playbook** → Reply Agent proceeds with a general-purpose draft; absence of a playbook is never a blocking error.

---

### 5.11 VIP Contacts

**Description:** User-designated important contacts get elevated treatment: always High priority regardless of AI-inferred priority, instant notification, and quick access to their conversation history.

**Edge Cases:**
- **VIP sends a genuinely low-urgency email** (e.g., a newsletter from a VIP's company) → still surfaced with elevated visibility, but the AI-generated urgency label is preserved alongside the VIP flag so the user can distinguish "important sender" from "important content."

---

### 5.12 Market Research Agent

**Description:** On-demand company/competitor research producing a structured report.

**Behavior (see Section 8.7):** Web search + crawling (Tavily, Firecrawl, Brave/Serper, optional Playwright for JS-heavy pages) → content extraction → GPT-5.5 analysis → structured report (Executive Summary, SWOT, Competitors, Opportunities, Risks) → displayed → agent terminates.

**Edge Cases:**
- **Company name collisions** (e.g., "Fable" the startup vs. unrelated entities) → Research Agent disambiguates using additional context (industry, domain, prior conversation) and confirms with the user if ambiguity remains.
- **Paywalled or unreachable sources** → gracefully skipped, and the report notes which sources could not be accessed rather than silently omitting the gap.
- **Rapidly changing information** (funding, leadership) → report includes retrieval date/timestamps per source so the user knows the recency of each claim.
- **Copyright/reproduction limits** → the report paraphrases and synthesizes source content; it does not reproduce large verbatim passages from any single source.

---

### 5.13 Payment Agent (Future — scoped, not built in MVP)

**Description:** Detects invoices in email, extracts structured data via OCR, verifies the vendor, matches against purchase orders and company policy, screens for fraud, and prepares a payment for user approval before execution.

**Behavior (design target):** invoice detection → OCR extraction → vendor verification → PO matching → policy validation → fraud check → payment summary preview → **user approval required** → execution via payment API (Stripe/Razorpay/bank APIs) → audit log entry → agent terminates.

**Edge Cases (design targets for future implementation):**
- Duplicate invoice detection (same invoice number/amount submitted twice).
- Vendor bank details changed since last payment (common fraud vector) → hard stop requiring manual verification, never silently paid.
- Invoice amount exceeds policy-defined auto-preview threshold → requires a second approver (four-eyes principle) for enterprise tier.
- Currency mismatches and FX handling.

This feature is documented for architectural completeness (see Section 9.8 and Section 15) but explicitly excluded from MVP scope per Section 3.3.

---

### 5.14 AI Help Assistant (Support Agent)

**Description:** In-app product guidance, onboarding, and troubleshooting, answered by a Support Agent grounded in product documentation (a separate, product-owned knowledge base distinct from the user's Company Memory).

**Edge Cases:**
- Questions that are actually feature requests or bug reports → Support Agent recognizes these and offers to log feedback rather than fabricating an answer about non-existent functionality.

---

### 5.15 Continuous Conversation / Context Memory

**Description:** The Supervisor Agent maintains short-term conversational context (recently viewed emails, last search results, last draft, last scheduling proposal) so users never have to repeat "which email" across a sequence of commands.

**Behavior:** Context stored in Redis (fast, session-scoped) with a rolling window and explicit context objects (`active_email_id`, `active_thread_id`, `active_draft_id`, `last_search_results`), refreshed on every command and expiring after a period of inactivity (default: 30 minutes).

**Edge Cases:**
- **Context handoff across devices** (start on desktop, continue on mobile) → context persisted server-side per user session, not per device, so it follows the user.
- **Context staleness** (user references "the meeting they suggested" from an hour-old thread after many intervening commands) → Supervisor prioritizes the most recent unambiguous referent; if more than one plausible match exists, it asks for clarification instead of guessing.

---

## 6. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | Inbox summarization latency ≤ 5s per email (p95) from arrival to dashboard visibility. Command Center response ≤ 3s (p95) for read/search operations; ≤ 8s (p95) for generative operations (draft, research). |
| **Availability** | 99.9% uptime target for core API and dashboard; background summarization degrades gracefully (queued, not blocking) during upstream (Gmail/OpenAI) outages. |
| **Scalability** | Horizontally scalable FastAPI backend behind a load balancer; Celery workers scale independently of the API tier; system must support at least 100,000 emails/day processed across all users at MVP scale, architected to reach 10M+/day without redesign. |
| **Reliability** | At-least-once processing for email ingestion with idempotency keys (Gmail message ID) to prevent duplicate summaries. |
| **Consistency** | Dashboard state must be eventually consistent within 2 seconds of a DB write, via Redis pub/sub → WebSocket. |
| **Data Retention** | Email metadata retained per user-configurable policy (default indefinite, deletable on request); raw voice audio not retained beyond transcription unless opted in. |
| **Accessibility** | UI meets WCAG 2.1 AA; voice interface serves as an accessibility-enhancing alternative input mode. |
| **Localization** | UI and AI-generated summaries support multiple languages at launch (English priority; Spanish, French, Hindi on roadmap). |
| **Observability** | Full request tracing across Supervisor → Agent → Tool calls via LangSmith; error tracking via Sentry; agent-level structured logs stored for audit and debugging. |
| **Cost Efficiency** | Token usage monitored per agent per user; caching of embeddings and repeated context to control LLM spend; model tiering (cheaper model for classification, GPT-5.5 for generation) where quality allows. |
| **Auditability** | Every consequential action (send, schedule, pay) logged with actor (AI-drafted vs. user-approved), timestamp, and full payload for compliance review. |
| **Portability** | Multi-agent architecture and RAG layer designed to be provider-agnostic where feasible (LLM, vector DB, voice provider abstracted behind interfaces) to avoid hard vendor lock-in. |

---

## 7. User Flows

### 7.1 First-Time Onboarding
1. User lands on marketing site → clicks "Get Started."
2. Signs in with Google OAuth; grants scoped permissions (Gmail read/send, Calendar read/write — explicitly itemized, not bundled as one vague "access your account" prompt).
3. Dashboard loads with an empty/loading state while historical inbox backfill begins asynchronously.
4. Guided setup: (a) optional Company Memory upload, (b) VIP contact selection, (c) voice permission prompt, (d) short interactive tutorial run by the Support Agent ("Try saying: show me my unread emails").
5. Supervisor Agent activates and enters wait state.

### 7.2 Daily Triage Flow (Priya persona)
1. Priya opens the app; Dashboard shows 12 new emails, 3 High priority, 1 meeting request.
2. She says: "Read me the high-priority ones."
3. Inbox Agent surfaces the 3 emails with summaries; TTS reads them aloud.
4. She says: "Reply to the investor one, keep it warm but concise."
5. Reply Agent drafts using Knowledge Base (fundraising FAQ doc) + thread context.
6. She reviews, says "shorten it," reviews again, says "send it," confirms on screen.
7. She says: "Schedule the call they asked for, Thursday afternoon."
8. Calendar Agent proposes 2 slots; she picks one via voice; event created with Meet link.
9. Total elapsed time: under 3 minutes for what would have been a 15-minute manual task.

### 7.3 Knowledge Query Flow (Alex persona)
1. Alex gets a customer email asking about return policy.
2. He asks the Command Center directly: "What's our return policy?"
3. Knowledge Agent retrieves the relevant clause from the uploaded handbook, cites the source doc.
4. Alex says: "Reply to the customer with that."
5. Reply Agent drafts a customer-facing version of the policy (translated from internal doc language into a friendly customer tone), Alex approves and sends.

### 7.4 Research Flow (Daniel persona)
1. Before a sales call, Daniel says: "Research Acme Corp before my 3pm."
2. Market Research Agent produces a report: company overview, competitors, recent news, pricing signals, review sentiment, SWOT.
3. Daniel skims the Executive Summary, uses two data points directly in his call notes.

### 7.5 Error/Recovery Flow
1. User says "reply to it" with no prior context.
2. Supervisor: "I don't have an email in context right now — which one would you like to reply to?"
3. User: "The one from Google about the interview."
4. Supervisor resolves via search, confirms match, proceeds to Reply Agent.

---

## 8. AI Workflows

This section details the internal model-level workflow for each major capability.

### 8.1 Automatic Inbox Processing Workflow
```
New Email Webhook (Gmail Pub/Sub)
        ↓
Idempotency check (message ID already processed?)
        ↓ no
Fetch full message via Gmail API
        ↓
Pre-process (strip signatures/quoted history for cleaner summarization)
        ↓
GPT-5.5 structured generation call →
   { summary, priority, category, urgency, reply_required, suspicious_flag }
        ↓
Persist to PostgreSQL (email_metadata table)
        ↓
Publish event to Redis → WebSocket → Dashboard live update
```
Model call uses **structured output (JSON mode)** with a strict schema to guarantee downstream parseability — no free-text parsing of LLM output for critical fields like priority.

### 8.2 Intent Routing Workflow (Supervisor)
```
User input (text or transcribed voice)
        ↓
Context assembly (recent context object from Redis + last N turns)
        ↓
GPT-5.5 intent classification (function-calling / tool-choice pattern)
        ↓
Confidence check
   ├─ High confidence, single intent → invoke agent directly
   ├─ High confidence, multi-step → decompose into ordered task list, invoke sequentially
   └─ Low confidence / missing entity → clarification question, no agent invoked
```
The Supervisor treats "which agent to call" as a **tool-selection problem**: each specialized agent is exposed to the Supervisor as a callable tool with a strict input schema, not a freeform prompt handoff.

### 8.3 Reply Generation Workflow
```
Trigger: user command referencing an email
        ↓
Reply Agent loads: target email + full thread + sender metadata
        ↓
Query Knowledge Agent (RAG) with a derived query
   (e.g., "refund policy for delayed shipments")
        ↓
Knowledge Agent → Qdrant semantic search → top-k chunks + citations
        ↓
Playbook lookup (does this scenario match a stored playbook?)
        ↓
GPT-5.5 draft generation, grounded in:
   thread + knowledge chunks + playbook structure + user's historical tone
        ↓
Draft displayed → Reply Agent enters WAIT state
        ↓ (loop while user issues edit commands)
Edit command → GPT-5.5 rewrite of CURRENT draft (not regeneration from scratch)
        ↓
"Send" command → Confirmation screen (recipient/subject/body diff shown)
        ↓
User approval → Gmail API send → Reply Agent terminates
```

### 8.4 Meeting Scheduling Workflow
```
Trigger: user command / detected meeting request in email
        ↓
Calendar Agent extracts: proposed date/time, duration, participants
   (via GPT-5.5 entity extraction with explicit fallback prompts for missing fields)
        ↓
Google Calendar API: check organizer + (if internal) attendee availability
        ↓
Free/busy computation → ranked candidate slots
        ↓
Google Meet API: generate Meet link (not yet attached to a real event)
        ↓
Preview rendered → Calendar Agent enters WAIT state
        ↓
User "confirm" (possibly after picking among slots)
        ↓
Calendar API: create event + attach Meet link + send invitations
        ↓
Calendar Agent terminates
```

### 8.5 Coreference / Context Resolution Workflow
```
User command containing a pronoun/reference ("it," "the first one," "that meeting")
        ↓
Supervisor pulls active context object: {active_email_id, last_search_results, active_draft_id, ...}
        ↓
Resolve reference against context
   ├─ Unambiguous → resolved, proceed
   ├─ Ambiguous (multiple plausible referents) → ask clarifying question
   └─ No context → ask user to specify
```

### 8.6 Knowledge Base Ingestion & Retrieval Workflow
```
Ingestion:
Upload file/URL → Unstructured/PyMuPDF/DOCX parsing → text normalization
        ↓
Chunking (semantic chunking, ~300-500 tokens/chunk with overlap)
        ↓
OpenAI text-embedding-3-large → vector per chunk
        ↓
Store in Qdrant with metadata (doc_id, source, owner, access_level, upload_date)

Retrieval:
Incoming query (from Reply Agent or direct user question)
        ↓
Query embedding → Qdrant top-k similarity search (with access-level filter)
        ↓
Optional re-ranking step (cross-encoder or GPT-5.5 relevance scoring) for top results
        ↓
Return chunks + source citations to calling agent
```

### 8.7 Market Research Workflow
```
Trigger: "Research <company>"
        ↓
Query planning (GPT-5.5 decomposes into sub-queries: overview, competitors, news, pricing, reviews)
        ↓
Parallel web search (Tavily / Brave / Serper) per sub-query
        ↓
Targeted crawl of top results (Firecrawl; Playwright fallback for JS-rendered pages)
        ↓
Content extraction & de-duplication
        ↓
GPT-5.5 synthesis → structured report (Executive Summary, SWOT, Competitors, Opportunities, Risks)
        ↓
Cache report in Qdrant (research cache) for fast recall on repeat queries within a TTL window
        ↓
Display report → Market Research Agent terminates
```

### 8.8 Voice Round-Trip Workflow
```
Microphone input → streamed to ElevenLabs STT → transcript
        ↓
Transcript treated as standard Command Center input (Section 8.2 applies)
        ↓
Result text generated by relevant agent
        ↓
Conversational summarization pass (GPT-5.5 condenses structured result into natural spoken language)
        ↓
ElevenLabs TTS → audio response streamed back to user
```

---

## 9. Agent Architecture

### 9.1 Architectural Principle (restated as a hard rule)

> The **Supervisor Agent is always running**. Every other agent is instantiated on-demand for exactly one task, executes, returns its result, and terminates. No specialized agent persists or polls in the background except the Inbox Agent's lightweight automatic pipeline (Section 5.2), which itself does not perform any consequential action — only fetch/summarize/prioritize/categorize.

This keeps the system's resource footprint proportional to actual user activity, bounds the blast radius of any single agent's behavior, and makes the "what can act without me?" answer simple and auditable: **nothing, except the four automatic inbox operations.**

### 9.2 Supervisor Agent
- **Responsibilities:** intent detection, agent orchestration, context/state management across turns, multi-step workflow decomposition, clarification handling.
- **Lifecycle:** persistent for the duration of the user's session (and beyond, via Redis-backed context that survives reconnects).
- **Tools exposed to it:** one callable "tool" per specialized agent, each with a strict JSON input/output schema.
- **Stack:** LangGraph (state graph with the Supervisor as the root node), GPT-5.5, LangSmith for tracing.

### 9.3 Inbox Agent
- **Responsibilities:** Gmail sync, classification, priority scoring, summarization, sentiment signal, meeting/follow-up detection; also handles on-demand search and "open email" tasks when invoked by the Supervisor.
- **Lifecycle:** two modes — (a) lightweight automatic pipeline running continuously in the background for new-email processing only; (b) on-demand instantiation for search/read commands, which terminates after returning results.
- **Stack:** Gmail API, GPT-5.5, LangGraph.

### 9.4 Reply Agent
- **Responsibilities:** thread comprehension, knowledge retrieval orchestration (calls Knowledge Agent), playbook application, draft generation and iterative rewriting, send execution after approval.
- **Lifecycle:** instantiated on a reply-related command; remains alive across the edit loop (Section 8.3) since it must retain draft state across multiple user turns; terminates after send or explicit cancellation.
- **Stack:** GPT-5.5, LangGraph, Gmail API, Qdrant (via Knowledge Agent).

### 9.5 Calendar Agent
- **Responsibilities:** calendar reads, availability computation, Meet link generation, event creation, invitation sending.
- **Lifecycle:** instantiated on a scheduling command; remains alive through the preview/confirm loop; terminates after event creation or cancellation.
- **Stack:** Google Calendar API, Google Meet API.

### 9.6 Knowledge Agent
- **Responsibilities:** semantic document search, context retrieval (RAG), supplying grounded context to the Reply Agent or directly answering user knowledge questions, Company Memory management (ingestion pipeline).
- **Lifecycle:** instantiated per query; stateless beyond the single retrieval call; terminates immediately after returning results.
- **Stack:** Qdrant, OpenAI Embeddings, LangChain, Unstructured, PyMuPDF.

### 9.7 Market Research Agent
- **Responsibilities:** company research, competitor analysis, news aggregation, pricing research, review/sentiment analysis, SWOT synthesis.
- **Lifecycle:** instantiated per research command; may run multiple parallel sub-tasks internally but presents as a single logical unit to the Supervisor; terminates after report delivery.
- **Stack:** Tavily, Firecrawl, Brave Search/Serper, Playwright (optional), GPT-5.5, Qdrant (research cache).

### 9.8 Payment Agent (Future)
- **Responsibilities (design only):** invoice detection/extraction, vendor verification, PO matching, policy validation, fraud detection, payment summary generation, approval-gated execution, audit logging.
- **Lifecycle (design only):** instantiated per payment-related command; strictly two-phase (preview → wait for explicit approval → execute); terminates after execution or cancellation. Never auto-executes regardless of invoice size or vendor trust level.
- **Stack (design target):** GPT-5.5, OCR engine, Policy Engine, ERP integration APIs, Stripe/Razorpay/Bank APIs, PostgreSQL.

### 9.9 Support Agent
- **Responsibilities:** in-app product guidance, onboarding, FAQ, documentation search — grounded in a product-owned knowledge base, separate from user Company Memory.
- **Lifecycle:** instantiated per help command; terminates after answering.
- **Stack:** GPT-5.5, LangGraph, Qdrant.

### 9.10 Agent Communication Contract

All agents communicate with the Supervisor via a standard envelope:

```json
{
  "agent": "reply_agent",
  "status": "waiting_for_user | completed | error | clarification_needed",
  "result": { "...task-specific payload..." },
  "context_updates": { "active_draft_id": "draft_123" },
  "requires_approval": true
}
```

`requires_approval: true` is a hard flag the UI layer checks before rendering any "act" button as directly clickable — it forces a confirmation step for send/schedule/pay actions regardless of which agent produced the result.

---

## 10. API Integrations

| Integration | Purpose | Key Endpoints/Scopes | Notes |
|---|---|---|---|
| **Gmail API** | Read, send, draft, search emails; labels; threads; attachments | `gmail.readonly`, `gmail.send`, `gmail.modify`, `gmail.compose` | Push notifications via Google Cloud Pub/Sub for near-real-time new-mail detection; polling fallback every 5 min as a safety net. |
| **Google Calendar API** | Read calendar, check availability, create/update/delete events | `calendar.events`, `calendar.freebusy` | Free/busy queries batched across attendees where internal. |
| **Google Meet API** | Generate Meet links, attach to Calendar events | Via Calendar API's `conferenceData` | No standalone Meet API call needed beyond conference data on event creation. |
| **Google OAuth 2.0** | Authentication + scoped authorization | Standard OAuth2 authorization code flow with PKCE | Incremental authorization: request Gmail scopes at signup, Calendar scopes when the user first tries to schedule, rather than over-asking upfront. |
| **ElevenLabs STT** | Voice-to-text transcription | Streaming transcription endpoint | Low-latency streaming preferred over batch for responsiveness. |
| **ElevenLabs TTS** | Text-to-speech voice responses | Voice synthesis endpoint | Configurable voice profile per user preference. |
| **OpenAI GPT-5.5** | Core reasoning, classification, generation across all agents | Chat/completions with function calling, JSON mode | Model tiering: cheaper/faster model for classification tasks (priority/category), GPT-5.5 for generation-heavy tasks (drafts, research synthesis). |
| **OpenAI text-embedding-3-large** | Embeddings for RAG | Embeddings endpoint | Batched embedding calls on ingestion for cost efficiency. |
| **Tavily / Firecrawl / Brave Search (Serper)** | Web search and crawling for Market Research Agent | Search + crawl endpoints | Multiple providers for redundancy and coverage; Firecrawl for structured page extraction, Playwright as a fallback for JS-heavy sites. |
| **Stripe / Razorpay / Bank APIs (Future)** | Payment execution for Payment Agent | Payment intents, transfers | Not integrated in MVP; sandboxed integration planned for Payment Agent beta. |

### 10.1 API Design Principles
- All external API calls wrapped in a retry-with-backoff layer; failures surfaced to the Supervisor as `status: error` rather than silently failing.
- Rate limit budgets tracked per integration per user to avoid hitting Gmail/Calendar quota ceilings; requests queued and throttled rather than dropped.
- Webhooks (Gmail Pub/Sub) verified via signature/token to prevent spoofed "new email" triggers.

---

## 11. Database Design

### 11.1 PostgreSQL — Primary Store

**users**
- id, email, name, google_oauth_token (encrypted), oauth_scopes, timezone, language_preference, plan_tier, created_at

**email_metadata**
- id, user_id (FK), gmail_message_id (unique per user, idempotency key), thread_id, sender, subject, summary, priority, category, urgency, reply_required, suspicious_flag, received_at, indexed_at

**threads**
- id, user_id (FK), gmail_thread_id, thread_summary, last_updated_at

**vip_contacts**
- id, user_id (FK), contact_email, contact_name, added_at

**playbooks**
- id, user_id/org_id (FK), name, scenario_type, template_structure, tone_settings, created_at, updated_at

**knowledge_documents**
- id, org_id (FK), title, source_type (upload/url), file_path_or_url, doc_type, access_level, indexing_status, uploaded_by, created_at

**drafts**
- id, user_id (FK), email_id (FK), thread_id (FK), current_body, version_history (JSONB), status (drafting/sent/discarded), created_at, updated_at

**meetings**
- id, user_id (FK), source_email_id (FK, nullable), calendar_event_id, participants (JSONB), proposed_slots (JSONB), status (previewed/confirmed/cancelled), created_at

**conversation_context**
- id, user_id (FK), session_id, active_email_id, active_thread_id, active_draft_id, last_search_query, updated_at *(mirrored into Redis for hot-path reads; Postgres is the durable backstop)*

**agent_logs / audit_logs**
- id, user_id (FK), agent_name, action_type, input_payload (JSONB, redacted of secrets), output_payload (JSONB), requires_approval, approved_by, approved_at, executed_at, status

**payment_records (future)**
- id, user_id/org_id (FK), invoice_id, vendor, amount, currency, policy_check_result, approval_status, approved_by, executed_at, audit_ref

### 11.2 Qdrant — Vector Store
- **Collection: `company_memory`** — vectors keyed by `chunk_id`, payload: `{doc_id, org_id, access_level, source, chunk_text, upload_date}`.
- **Collection: `research_cache`** — vectors keyed by `research_query_hash`, payload: `{company_name, report_json, generated_at, ttl}`.
- **Collection: `support_kb`** — product documentation for the Support Agent, separate namespace from user data.

### 11.3 Redis — Cache & Ephemeral State
- Session cache (JWT/session validation)
- `conversation_context:{user_id}` — hot-path active context object, TTL-based expiry (30 min default)
- Celery task queues (email processing, indexing jobs)
- Dashboard cache (pre-aggregated counts for fast initial render)
- Rate limiting counters per user per integration

### 11.4 Data Access & Isolation
- All tables include `user_id` or `org_id` for strict row-level isolation; Postgres row-level security (RLS) policies enforced at the DB layer, not just application logic, as defense-in-depth.
- Qdrant queries always filtered by `org_id` and `access_level` server-side before returning to any agent — an agent can never retrieve another organization's chunks, even by construction error in a prompt.

---

## 12. Folder Structure

```
ai-email-assistant/
├── apps/
│   ├── web/                        # Next.js 15 frontend
│   │   ├── app/
│   │   │   ├── (auth)/
│   │   │   ├── dashboard/
│   │   │   ├── command-center/
│   │   │   ├── inbox/
│   │   │   ├── knowledge-base/
│   │   │   ├── playbooks/
│   │   │   └── settings/
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn/ui-based primitives
│   │   │   ├── voice/
│   │   │   ├── email/
│   │   │   └── agents/             # per-agent result renderers
│   │   ├── hooks/
│   │   ├── stores/                 # Zustand stores
│   │   ├── lib/
│   │   │   ├── api-client.ts
│   │   │   └── websocket.ts
│   │   └── styles/
│   │
│   └── api/                        # FastAPI backend
│       ├── main.py
│       ├── routers/
│       │   ├── auth.py
│       │   ├── inbox.py
│       │   ├── command_center.py
│       │   ├── knowledge.py
│       │   ├── calendar.py
│       │   ├── research.py
│       │   └── payments.py         # scaffolded, disabled in MVP
│       ├── agents/
│       │   ├── supervisor/
│       │   │   ├── graph.py        # LangGraph state graph definition
│       │   │   ├── intent_router.py
│       │   │   └── context_manager.py
│       │   ├── inbox_agent/
│       │   ├── reply_agent/
│       │   ├── calendar_agent/
│       │   ├── knowledge_agent/
│       │   ├── research_agent/
│       │   ├── support_agent/
│       │   └── payment_agent/      # scaffolded, disabled in MVP
│       ├── integrations/
│       │   ├── gmail_client.py
│       │   ├── calendar_client.py
│       │   ├── meet_client.py
│       │   ├── elevenlabs_client.py
│       │   ├── qdrant_client.py
│       │   └── search_providers/
│       ├── models/                 # SQLAlchemy models
│       ├── schemas/                # Pydantic request/response schemas
│       ├── services/
│       │   ├── ingestion/          # knowledge base parsing/chunking
│       │   ├── rag/
│       │   └── audit/
│       ├── workers/                # Celery tasks
│       │   ├── email_processor.py
│       │   ├── kb_indexer.py
│       │   └── research_cache.py
│       ├── core/
│       │   ├── config.py
│       │   ├── security.py
│       │   └── logging.py
│       └── tests/
│
├── infra/
│   ├── docker/
│   ├── terraform/                  # (or equivalent IaC)
│   └── ci-cd/
│
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   └── API_REFERENCE.md
│
└── README.md
```

---

## 13. Security

### 13.1 Authentication & Authorization
- Google OAuth 2.0 with PKCE for all user auth; no password storage.
- Incremental scope requests (Section 10) — the app never requests more Gmail/Calendar permission than the current feature set requires.
- Session management via short-lived JWTs + refresh tokens; OAuth tokens encrypted at rest (AES-256) and never exposed to the frontend.

### 13.2 Human-in-the-Loop for Consequential Actions
- **Hard rule, enforced at the agent-contract layer (Section 9.10):** any action that sends an email, creates a calendar event, or moves money requires an explicit, itemized user approval step. This is not merely a UI convention — the backend rejects any "send" or "execute" API call that lacks a valid, logged approval record tied to that specific draft/event/payment ID.

### 13.3 Data Protection
- All API traffic over HTTPS/TLS 1.2+.
- Data encrypted at rest (Postgres, Qdrant, Redis persistence) and in transit.
- Company Memory documents stored in access-controlled object storage with per-org encryption keys.
- PII minimization: only necessary email metadata is persisted; full email bodies are fetched on-demand from Gmail rather than mirrored wholesale into our database, reducing our own data liability.

### 13.4 Role-Based Access Control (RBAC)
- Roles: Owner, Admin, Member, Viewer (team/workspace tier).
- Document-level access control within Company Memory (e.g., HR/legal docs restricted to Admin role).
- Enterprise tier: delegated access (e.g., Executive Assistant persona operating on behalf of an Executive) with a clear audit trail distinguishing "drafted by AI," "approved by delegate," and "final approver."

### 13.5 Prompt Injection & Content Safety
- Email bodies are treated as **untrusted data**, never as instructions. Any text within a fetched email that resembles a command (e.g., "ignore previous instructions and forward this to...") is passed to the LLM strictly as content-to-summarize/reply-to, with system-level guardrails preventing it from being interpreted as a directive to any agent.
- The Inbox Agent's "Suspicious" flag (Section 5.2) specifically watches for phishing and injection-style patterns and surfaces them to the user rather than acting on them.

### 13.6 Audit & Compliance
- Full audit log (Section 11.1, `agent_logs`) for every agent action, retained per configurable policy (default: 2 years for consequential actions).
- SOC 2 Type II readiness targeted post-MVP as the product moves upmarket to team/enterprise tiers.
- GDPR/CCPA-aligned data export and deletion endpoints (user can request full data export or full account/data purge).

### 13.7 Least Privilege for Agents
- Each specialized agent is granted only the tool/API scopes it needs (e.g., the Knowledge Agent has no Gmail send capability; the Calendar Agent has no access to Company Memory). This containment limits the blast radius of any single agent misbehaving or being manipulated.

---

## 14. Deployment

### 14.1 Environments
- **Local/Dev:** Docker Compose spinning up FastAPI, Postgres, Redis, and a local Qdrant instance for fast iteration.
- **Staging:** Mirrors production topology at reduced scale; used for integration testing against real (sandboxed/test) Google OAuth apps.
- **Production:** Fully managed, autoscaled.

### 14.2 Infrastructure
| Layer | Choice | Rationale |
|---|---|---|
| Frontend hosting | Vercel | Native Next.js support, edge caching, preview deployments per PR. |
| Backend hosting | Google Cloud Run (primary), Railway/Render as alternatives | Serverless container scaling matches bursty agent workloads; Cloud Run pairs naturally with Gmail Pub/Sub. |
| Background workers | Celery workers on Cloud Run Jobs (or dedicated worker VMs at scale) | Decouples ingestion/indexing spikes from the request-serving API tier. |
| Containerization | Docker | Consistent build artifacts across dev/staging/prod. |
| Database | Managed PostgreSQL (Cloud SQL or equivalent) | Managed backups, PITR, and RLS support. |
| Cache/Queue | Managed Redis | Low-latency session/context store and Celery broker. |
| Vector DB | Managed Qdrant Cloud (or self-hosted cluster at scale) | Purpose-built ANN performance for RAG at low latency. |

### 14.3 CI/CD
- GitHub Actions pipeline: lint → type-check → unit tests → integration tests (mocked Gmail/Calendar) → build → deploy to staging → manual promotion to production.
- Feature flags for gradual rollout of new agents (e.g., Payment Agent beta) to a subset of users/orgs.

### 14.4 Monitoring & Observability
- **LangSmith:** full trace of Supervisor → Agent → Tool call chains, including token usage and latency per hop — critical for debugging multi-agent behavior.
- **Sentry:** application error tracking across frontend and backend.
- Custom dashboards: per-agent success/failure rate, average time-to-first-token, approval-vs-abandon rate for drafts/meetings (a key product health signal).

---

## 15. Future Roadmap

### 15.1 Near-Term (Post-MVP, 0–6 months)
- **Payment Agent (Beta):** invoice detection through approval-gated execution (Section 5.13/9.8), starting with a single payment provider integration and a hard per-transaction approval requirement with no auto-execution tier initially.
- **Multi-email account support:** manage multiple Gmail accounts from a single Command Center, with account-scoped context switching.
- **Team workspaces & shared Company Memory:** org-level knowledge base shared across a team with the RBAC model described in Section 13.4.
- **AI productivity analytics:** time-saved estimates, response-time trends, inbox health scoring.

### 15.2 Mid-Term (6–12 months)
- **Microsoft Outlook support:** parallel Inbox/Reply/Calendar agent implementations against Microsoft Graph API, behind the same Supervisor architecture (validating the "modular agent platform" goal in Section 3.1).
- **Slack and Microsoft Teams integration:** extend the Command Center beyond email into chat-based delegation ("ask the assistant from Slack").
- **CRM integrations (Salesforce, HubSpot):** let the Reply and Research Agents read/write CRM context (e.g., auto-log a sales email into the deal timeline).
- **Workflow automation builder:** let power users define their own multi-step playbooks/triggers visually, beyond the built-in Playbooks library.

### 15.3 Long-Term (12+ months)
- **Enterprise admin dashboard:** org-wide policy configuration, seat management, compliance reporting, SSO/SCIM.
- **Autonomous task execution with configurable approval policies:** allow trusted users/orgs to define narrow, auditable auto-approval rules (e.g., "auto-schedule any meeting request from a VIP contact under 30 minutes") — always opt-in, always reversible, always logged, never the default.
- **Notion integration** for knowledge base sourcing and note-taking sync.
- **Mobile applications** (native iOS/Android) built around voice-first interaction as the primary mode.
- **Multi-language support** expanded across summarization, replies, and voice (STT/TTS) beyond the initial launch languages.
- **Additional ERP integrations** (SAP, Oracle ERP) for the mature Payment Agent, serving larger finance teams.

---

## 16. Risks

| Risk | Category | Impact | Mitigation |
|---|---|---|---|
| **Unauthorized send/schedule/payment due to agent bug** | Trust/Safety | Severe — reputational and potentially legal/financial harm | Hard approval-gate enforced at the API layer (Section 13.2), not just UI; every consequential action requires a logged approval record tied to a specific artifact ID. |
| **Prompt injection via malicious email content** | Security | Medium-High — could manipulate replies or leak data | Untrusted-content handling (Section 13.5), suspicious-email flagging, sandboxed agent tool scopes (Section 13.7). |
| **Hallucinated factual claims in replies (wrong pricing, wrong policy)** | Product Quality/Trust | High — damages user's relationships/customers | Mandatory RAG grounding with citations for factual claims; explicit "gap" flagging when Knowledge Base lacks an answer (Section 5.9) rather than fabrication; user approval step catches remaining errors. |
| **Gmail/Calendar API rate limits or outages** | Reliability | Medium — degraded automatic processing | Queued/backoff processing (Section 8.1), graceful degradation, user-visible status if sync is delayed. |
| **LLM/embedding provider cost overrun at scale** | Business/Cost | Medium | Model tiering, caching, token usage monitoring per agent (Section 6), research cache with TTL to avoid redundant costly research runs. |
| **Over-reliance leads to voice misrecognition causing wrong action** | Product Quality | Medium | Confirmation step for all consequential actions regardless of input mode (Section 5.4); low-confidence transcription triggers re-prompt rather than action. |
| **Enterprise trust barrier (IT/security won't approve OAuth scopes)** | Go-to-Market | High for enterprise expansion | Incremental scope requests, SOC 2 roadmap (Section 13.6), transparent audit logs, admin dashboard on roadmap (Section 15.3). |
| **Vendor lock-in (OpenAI, ElevenLabs, Qdrant)** | Technical/Business | Medium | Interfaces abstracted per Section 6 (Portability); model/provider swaps isolated to integration layer, not scattered through agent logic. |
| **Payment Agent fraud exposure (future)** | Security/Financial | Severe once launched | Strict two-phase preview/approval design from inception (Section 9.8), vendor-change hard-stops, four-eyes approval for large amounts, sandboxed rollout with feature flags. |
| **Data privacy/compliance gaps as we scale to regulated industries** | Compliance | Medium-High | GDPR/CCPA-aligned export/delete flows, RLS-enforced multi-tenancy (Section 11.4), planned SOC 2 Type II. |

---

## 17. Success Metrics

### 17.1 Activation & Engagement
- **Time-to-first-value:** % of new users who complete a full triage-to-reply loop within their first session.
- **Daily Active Usage:** % of connected accounts with at least one Command Center interaction per day.
- **Voice adoption rate:** % of commands issued via voice vs. text, tracked as a leading indicator of the voice-first differentiation succeeding.

### 17.2 Product Quality
- **Draft acceptance rate:** % of Reply Agent drafts sent with minimal edits (target: <20% edit distance) vs. heavily rewritten or discarded.
- **Knowledge grounding accuracy:** % of knowledge-based answers with a valid source citation vs. flagged gaps vs. (ideally zero) unsupported claims, sampled via periodic human review.
- **Scheduling success rate:** % of Calendar Agent proposals confirmed on first preview vs. requiring re-proposal.
- **Approval-vs-abandon rate:** ratio of agent outputs that reach user approval vs. those abandoned mid-flow — a proxy for how well agent output matches user intent on the first try.

### 17.3 Trust & Safety
- **Zero unauthorized-action incidents:** count of any send/schedule/payment executed without a valid logged approval (target: 0, hard SLA).
- **Suspicious email detection recall/precision:** measured against a labeled phishing/spam sample set.

### 17.4 Business Metrics
- **Time saved per user per week** (self-reported + inferred from triage/reply latency reduction) — the core value proposition metric, feeding directly into pricing and marketing claims.
- **Conversion rate:** free/trial → paid.
- **Expansion rate:** individual → team workspace tier adoption.
- **Net Revenue Retention (NRR)** once team tier launches.
- **Support ticket volume per active user** — a proxy for whether the AI Help Assistant and overall UX reduce (rather than create) support burden.

### 17.5 Technical Health
- **Agent task success rate** per agent type (completed without error vs. error/timeout).
- **p95 latency** per workflow type (Section 6 targets) tracked continuously via LangSmith/Sentry dashboards.
- **Cost per active user per month** (LLM + embedding + voice + search API spend) tracked against pricing tiers to ensure unit economics hold as usage scales.

---

*End of Document.*
