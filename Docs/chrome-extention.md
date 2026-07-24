# Chrome Extension Build Guide — AetherOS AI Assistant

**Audience:** Any engineer building the Chrome extension (`apps/extension/`)
**Companion documents:** `PRD.md`, `TECH_STACK.md`, `steps-frontend.md`, `steps-backend.md`
**Backend API repo:** `apps/api/` (FastAPI)
**Web frontend repo:** `apps/web/` (Next.js 16)

---

## Table of Contents

0. Architecture Overview & Key Design Decisions
1. Phase 0 — Scaffold Extension Project
2. Phase 1 — Manifest & Permissions
3. Phase 2 — Shared Types (mirror backend schemas)
4. Phase 3 — Auth Layer (Clerk in Chrome Extensions)
5. Phase 4 — API Client (all endpoints)
6. Phase 5 — WebSocket Client
7. Phase 6 — Zustand Store
8. Phase 7 — Side Panel UI
9. Phase 8 — Background Service Worker
10. Phase 9 — Voice Input
11. Phase 10 — Cross-Device Session Sharing
12. Phase 11 — Build & Package
13. Phase 12 — Verification Checklist
14. Appendix A — Complete API Reference
15. Appendix B — Complete Type Definitions
16. Appendix C — Environment Variables

---

## 0. Architecture Overview & Key Design Decisions

### 0.1 The extension is a new client to the same backend

**Zero backend changes needed.** The backend already:
- Has CORS set to `["*"]` (`apps/api/main.py:57-63`)
- Uses Bearer token auth (`Authorization: Bearer <clerk_jwt>`)
- Accepts WebSocket connections via query param (`/ws?token=<jwt>`)
- Returns consistent JSON error envelopes

### 0.2 Identity vs. Integration — Two Separate Concerns

| Layer | Purpose | Email |
|-------|---------|-------|
| **Clerk Auth** (`core/security.py`) | Login — who you are | Any email (e.g., `you@gmail.com`) |
| **Google OAuth** (`routers/integrations.py`) | Which inbox/calendar to automate | Any Gmail (e.g., `work@company.com`) |

These can be the **same or different** emails. They are stored in separate database tables (`users` vs `google_integrations`). A disconnected Google account does not log the user out.

### 0.3 Session Sharing Between Web & Extension

The backend's `POST /command` accepts a `session_id` (UUID, client-generated). The web app and extension each generate their **own** `session_id` — they have independent conversation threads. However, they access the **same user data** (inbox, drafts, meetings) because they authenticate as the same user.

This means:
- A draft created in the web app appears in the extension's draft list
- Emails synced by one client are visible to the other
- Conversation context is **per-client**, which is correct behavior

### 0.4 Tech Stack for the Extension

| Technology | Purpose |
|------------|---------|
| React 19 | UI framework |
| TypeScript | Type safety |
| Vite | Build tool |
| Zustand | Client state management |
| Clerk JS SDK | Authentication in extension context |
| Chrome Extension APIs | Storage, side panel, service worker |
| Web Audio API / MediaRecorder | Voice input |

---

## Phase 0 — Scaffold Extension Project

### 0.1 Create the folder structure

```bash
cd apps/extension
mkdir -p public/icons src/{background,sidepanel/{components,styles},lib,utils}
```

### 0.2 Initialize the project

```bash
npm create vite@latest . -- --template react-ts
npm install zustand lucide-react
npm install -D @types/chrome
```

### 0.3 Configure `vite.config.ts`

Chrome extensions need flat output (no code splitting, hashed filenames must be predictable for the manifest):

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        sidepanel: resolve(__dirname, 'src/sidepanel/index.html'),
        background: resolve(__dirname, 'src/background/service-worker.ts'),
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name].js',
        assetFileNames: '[name].[ext]',
      },
    },
    target: 'esnext',
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
});
```

### 0.4 Folder structure (final)

```
apps/extension/
├── public/
│   └── icons/
│       ├── icon-16.png
│       ├── icon-48.png
│       └── icon-128.png
├── src/
│   ├── background/
│   │   └── service-worker.ts
│   ├── sidepanel/
│   │   ├── index.html
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── AuthGate.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── Avatar.tsx
│   │   │   ├── Transcript.tsx
│   │   │   ├── CommandBar.tsx
│   │   │   ├── DraftCard.tsx
│   │   │   ├── CalendarCard.tsx
│   │   │   ├── VoiceButton.tsx
│   │   │   └── SettingsPanel.tsx
│   │   └── styles/
│   │       └── globals.css
│   ├── lib/
│   │   ├── api-client.ts
│   │   ├── websocket-client.ts
│   │   ├── auth.ts
│   │   ├── storage.ts
│   │   └── types.ts
│   └── utils/
│       └── audio.ts
├── package.json
├── tsconfig.json
├── vite.config.ts
└── .env
```

---

## Phase 1 — Manifest & Permissions

File: `public/manifest.json`

```json
{
  "manifest_version": 3,
  "name": "Aether — AI Email Assistant",
  "version": "1.0.0",
  "description": "AI Chief of Staff for your inbox — triage, draft replies, schedule meetings, and research companies.",
  "permissions": [
    "storage",
    "sidePanel",
    "alarms"
  ],
  "optional_permissions": [
    "audioCapture"
  ],
  "host_permissions": [
    "http://localhost:8000/*",
    "https://*.clerk.accounts.dev/*",
    "https://api.clerk.com/*"
  ],
  "side_panel": {
    "default_path": "sidepanel/index.html"
  },
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  "action": {
    "default_title": "Aether — Open Assistant",
    "default_icon": {
      "16": "icons/icon-16.png",
      "48": "icons/icon-48.png",
      "128": "icons/icon-128.png"
    }
  },
  "icons": {
    "16": "icons/icon-16.png",
    "48": "icons/icon-48.png",
    "128": "icons/icon-128.png"
  },
  "key": "aether-chrome-extension" 
}
```

**Critical permissions explained:**
- `storage` — stores Clerk JWT, session_id, and user preferences
- `sidePanel` — opens the side panel UI
- `alarms` — periodic polling for badge counts
- `audioCapture` (optional) — requested only when user first taps the mic button
- `host_permissions` — must match the backend URL (localhost for dev, your deployed URL for prod)

---

## Phase 2 — Shared Types

File: `src/lib/types.ts`

Mirror **every** backend schema from `apps/api/schemas/` exactly. These types are the contract between the extension and the backend.

```typescript
// ============================================================
// AUTH
// ============================================================

export interface AuthState {
  token: string | null;
  userId: string | null;
  email: string | null;
  isLoaded: boolean;
}

// ============================================================
// AGENT RESPONSE (mirrors schemas/agent_response_schema.py)
// ============================================================

export interface AgentResponse {
  agent: string;
  status: 'waiting_for_user' | 'completed' | 'error' | 'clarification_needed';
  result: Record<string, unknown>;
  context_updates: Record<string, unknown>;
  requires_approval: boolean;
}

export type AgentStatus = AgentResponse['status'];

// ============================================================
// COMMAND CENTER (POST /command, POST /command/voice)
// ============================================================

export interface CommandResponse {
  session_id: string;
  response: AgentResponse;
}

export interface VoiceCommandResponse extends CommandResponse {
  transcript: string;
}

// ============================================================
// EMAIL (mirrors EmailMetadataResponse from routers/inbox.py)
// ============================================================

export interface EmailMetadata {
  id: string;
  user_id?: string;
  gmail_message_id: string;
  thread_id?: string | null;
  sender: string;
  subject: string;
  summary?: string | null;
  priority: string;
  category: string;
  urgency: boolean;
  reply_required: boolean;
  suspicious_flag: boolean;
  received_at: string;
  indexed_at?: string;
}

// ============================================================
// DRAFTS (mirrors routers/replies.py responses)
// ============================================================

export interface DraftItem {
  id: string;
  email_id?: string | null;
  body: string;
  current_body?: string;
  version_history?: Record<string, unknown>[];
  status: string;
  has_gaps?: boolean;
  gap_notes?: string[];
  created_at?: string | null;
  recipient?: string | null;
  subject?: string | null;
  original_body?: string;
  original_received_at?: string | null;
}

export interface DraftCreateResponse {
  draft_id: string;
  email_id: string;
  body: string;
  version_history: Record<string, unknown>[];
  status: string;
  has_gaps: boolean;
  gap_notes: string[];
}

export interface DraftEditResponse {
  draft_id: string;
  body: string;
  version_history: Record<string, unknown>[];
  status: string;
}

export interface PrepareSendResponse {
  approval_id: string;
  draft_id: string;
  status: string;
  preview: {
    recipient: string;
    subject: string;
    body: string;
  };
}

// Active draft state used in the UI
export interface ActiveDraft {
  draft_id: string;
  draft_body: string;
  has_gaps?: boolean;
  gap_notes?: string[];
  recipient?: string;
  subject?: string;
  created_at?: string;
}

// ============================================================
// CALENDAR / MEETINGS (mirrors routers/calendar.py)
// ============================================================

export interface CalendarPreviewResponse {
  approval_id: string;
  preview_id: string;
  title: string;
  start: string;
  end: string;
  duration_minutes: number;
  participants: string[];
  meet_link?: string;
  double_booking_warnings?: unknown[];
  source_email?: {
    subject?: string;
    from?: { name?: string; email?: string };
    summary?: string;
    message_id?: string;
  };
}

export interface ActiveCalendarProposal {
  preview_id: string;
  approval_id?: string;
  title: string;
  start: string;
  end: string;
  duration_minutes?: number;
  attendees: string[];
  meet_link?: string;
  source_email?: CalendarPreviewResponse['source_email'];
  double_booking_warnings?: unknown[];
}

// ============================================================
// DASHBOARD (GET /dashboard/summary)
// ============================================================

export interface DashboardSummary {
  total_emails: number;
  high_priority: number;
  unread: number;
  recent_meetings: number;
  pending_approvals: number;
}

// ============================================================
// KNOWLEDGE (mirrors routers/knowledge.py)
// ============================================================

export interface KnowledgeDocument {
  id: string;
  org_id?: string | null;
  user_id?: string | null;
  title: string;
  source_type: string;
  file_path_or_url: string;
  doc_type: string;
  access_level: string;
  indexing_status: string;
  uploaded_by?: string | null;
  created_at: string;
}

export interface KnowledgeQueryResult {
  score: number;
  payload: Record<string, unknown>;
}

// ============================================================
// INTEGRATIONS (GET /integrations/google/status)
// ============================================================

export interface GoogleIntegrationStatus {
  connected: boolean;
  scopes: string[];
  is_expired?: boolean;
  revoked?: boolean;
  expires_at?: string;
}

// ============================================================
// USER / SETTINGS (GET /me, GET /settings/profile)
// ============================================================

export interface UserProfile {
  id: string;
  email: string;
  name?: string | null;
  timezone?: string | null;
  language_preference: string;
  plan_tier: string;
  created_at: string;
}

export interface UserPreferences {
  timezone?: string;
  language?: string;
  plan_tier?: string;
  voice_history_opt_in?: boolean;
}

// ============================================================
// PLAYBOOKS (mirrors routers/playbooks.py)
// ============================================================

export interface Playbook {
  id: string;
  user_id?: string | null;
  org_id?: string | null;
  name: string;
  scenario_type: string;
  template_structure: string;
  tone_settings?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

// ============================================================
// VIP CONTACTS (mirrors routers/vip_contacts.py)
// ============================================================

export interface VIPContact {
  id: string;
  user_id: string;
  contact_email: string;
  contact_name?: string | null;
  added_at: string;
}

// ============================================================
// WEB SOCKET EVENTS
// ============================================================

export interface WsConnectedEvent {
  type: 'connected';
  user_id: string;
  message: string;
}

export interface WsPongEvent {
  type: 'pong';
}

export interface WsDashboardEvent {
  type: 'new_email' | 'draft_created' | 'approval_needed' | 'meeting_proposal' | 'research_completed';
  [key: string]: unknown;
}

export type WsEvent = WsConnectedEvent | WsPongEvent | WsDashboardEvent;

// ============================================================
// TRANSCRIPT (conversation history in the UI)
// ============================================================

export interface TranscriptEntry {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agent_used?: string;
  timestamp: string;
  draft_id?: string;
  draft_body?: string;
  requires_approval?: boolean;
}

// ============================================================
// ERROR ENVELOPE (mirrors core/exceptions.py)
// ============================================================

export interface ApiError {
  error: {
    code: string;
    message: string;
    request_id: string;
    details?: Record<string, unknown>;
  };
}
```

---

## Phase 3 — Auth Layer

### 3.1 Architecture

Chrome extensions cannot use Clerk's React SDK directly (it expects a full browser context with page redirects). Instead, use Clerk's **standalone JavaScript SDK** with a custom popup flow.

**Flow:**
1. Extension opens a popup window pointing to Clerk's hosted sign-in page
2. User signs in (email/password, Google social login, magic link, etc.)
3. Clerk redirects back to a callback URL
4. Extension captures the session JWT from the callback
5. Token is stored in `chrome.storage.local`
6. All API calls attach `Authorization: Bearer <token>`

### 3.2 Auth Helper

File: `src/lib/auth.ts`

```typescript
import type { AuthState } from './types';

const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
const CLERK_SIGN_IN_URL = `https://${import.meta.env.VITE_CLERK_FRONTEND_API}/sign-in`;
const REDIRECT_URL = chrome.identity.getRedirectURL('clerk-callback');

// Storage keys
const STORAGE_KEY_TOKEN = 'clerk_session_token';
const STORAGE_KEY_USER = 'clerk_user_info';

export async function getStoredToken(): Promise<string | null> {
  const result = await chrome.storage.local.get(STORAGE_KEY_TOKEN);
  return result[STORAGE_KEY_TOKEN] || null;
}

export async function getStoredUserInfo(): Promise<{ userId: string; email: string } | null> {
  const result = await chrome.storage.local.get(STORAGE_KEY_USER);
  return result[STORAGE_KEY_USER] || null;
}

export async function setStoredAuth(token: string, userId: string, email: string): Promise<void> {
  await chrome.storage.local.set({
    [STORAGE_KEY_TOKEN]: token,
    [STORAGE_KEY_USER]: { userId, email },
  });
}

export async function clearStoredAuth(): Promise<void> {
  await chrome.storage.local.remove([STORAGE_KEY_TOKEN, STORAGE_KEY_USER]);
}

// Listen for auth changes across extension pages
export function onAuthChanged(callback: (token: string | null) => void): () => void {
  const listener = (changes: Record<string, chrome.storage.StorageChange>) => {
    if (changes[STORAGE_KEY_TOKEN]) {
      callback(changes[STORAGE_KEY_TOKEN].newValue || null);
    }
  };
  chrome.storage.onChanged.addListener(listener);
  return () => chrome.storage.onChanged.removeListener(listener);
}

// Open Clerk sign-in in a popup using chrome.identity.launchWebAuthFlow
export async function signInWithClerk(): Promise<AuthState> {
  return new Promise((resolve, reject) => {
    const authUrl = new URL(CLERK_SIGN_IN_URL);
    authUrl.searchParams.set('redirect_url', REDIRECT_URL);

    chrome.identity.launchWebAuthFlow(
      {
        url: authUrl.toString(),
        redirectUrl: REDIRECT_URL,
        interactive: true,
      },
      async (responseUrl) => {
        if (chrome.runtime.lastError || !responseUrl) {
          reject(new Error(chrome.runtime.lastError?.message || 'Sign in cancelled'));
          return;
        }

        // Parse the callback URL for the Clerk session JWT
        // Clerk typically returns the token as a hash fragment or query param
        const url = new URL(responseUrl);
        const sessionToken = url.hash
          ? new URLSearchParams(url.hash.slice(1)).get('clerk_session_jwt')
          : url.searchParams.get('clerk_session_jwt');

        if (!sessionToken) {
          reject(new Error('No session token in callback'));
          return;
        }

        // Decode the JWT payload to extract user info (without verification — backend verifies)
        const payload = JSON.parse(atob(sessionToken.split('.')[1]));
        const userId = payload.sub;
        const email = payload.email || payload.email_address || '';

        await setStoredAuth(sessionToken, userId, email);

        resolve({
          token: sessionToken,
          userId,
          email,
          isLoaded: true,
        });
      }
    );
  });
}

export async function signOut(): Promise<void> {
  await clearStoredAuth();
}

export async function getHeaders(): Promise<Record<string, string>> {
  const token = await getStoredToken();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// For API calls with FormData (no Content-Type needed, browser sets it)
export async function getFormHeaders(): Promise<Record<string, string>> {
  const token = await getStoredToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}
```

### 3.3 Background Service Worker Auth Handler

File: `src/background/service-worker.ts` (auth portion)

```typescript
import { getStoredToken, clearStoredAuth } from '../lib/auth';

// Track auth state
let currentToken: string | null = null;

// Initialize auth state from storage
async function initAuth() {
  currentToken = await getStoredToken();
}

initAuth();

// Listen for storage changes (sync from side panel login)
chrome.storage.onChanged.addListener((changes) => {
  if (changes.clerk_session_token) {
    currentToken = changes.clerk_session_token.newValue || null;
  }
});

// Message handler for auth from side panel
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'AUTH_UPDATED') {
    currentToken = message.token;
    sendResponse({ success: true });
  }
  if (message.type === 'GET_AUTH') {
    sendResponse({ token: currentToken });
  }
  return true; // async response
});
```

---

## Phase 4 — API Client

File: `src/lib/api-client.ts`

This is the centralized, typed API client. Every method mirrors a backend endpoint from `apps/api/routers/`.

```typescript
import { getFormHeaders, getHeaders } from './auth';
import type {
  CommandResponse,
  VoiceCommandResponse,
  EmailMetadata,
  DraftItem,
  DraftCreateResponse,
  DraftEditResponse,
  PrepareSendResponse,
  DashboardSummary,
  GoogleIntegrationStatus,
  UserProfile,
  UserPreferences,
  KnowledgeDocument,
  KnowledgeQueryResult,
  Playbook,
  VIPContact,
  CalendarPreviewResponse,
} from './types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ============================================================
// COMMAND CENTER
// ============================================================

export async function sendTextCommand(
  command: string,
  sessionId: string
): Promise<CommandResponse> {
  const headers = await getFormHeaders(); // no Content-Type for FormData
  const formData = new FormData();
  formData.append('command', command);
  formData.append('session_id', sessionId);

  const res = await fetch(`${API_URL}/command`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.error?.message || `Command failed: ${res.status}`);
  }

  return res.json();
}

export async function sendVoiceCommand(
  audioBlob: Blob,
  sessionId: string
): Promise<VoiceCommandResponse> {
  const headers = await getFormHeaders();
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');
  formData.append('session_id', sessionId);

  const res = await fetch(`${API_URL}/command/voice`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.error?.message || `Voice command failed: ${res.status}`);
  }

  return res.json();
}

// ============================================================
// INBOX
// ============================================================

export async function getEmails(params?: {
  priority?: string;
  category?: string;
  sender?: string;
  hours?: number;
  days?: number;
  limit?: number;
  offset?: number;
}): Promise<EmailMetadata[]> {
  const headers = await getHeaders();
  const searchParams = new URLSearchParams();
  if (params?.priority) searchParams.set('priority', params.priority);
  if (params?.category) searchParams.set('category', params.category);
  if (params?.sender) searchParams.set('sender', params.sender);
  if (params?.hours) searchParams.set('hours', String(params.hours));
  if (params?.days) searchParams.set('days', String(params.days));
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.offset) searchParams.set('offset', String(params.offset));

  const res = await fetch(`${API_URL}/inbox/emails?${searchParams.toString()}`, { headers });
  if (!res.ok) throw new Error(`Failed to fetch emails: ${res.status}`);
  return res.json();
}

export async function searchEmails(query: {
  q: string;
  page_token?: string;
  limit?: number;
  hours?: number;
  days?: number;
  sender?: string;
}): Promise<EmailMetadata[]> {
  const headers = await getHeaders();
  const searchParams = new URLSearchParams({ q: query.q });
  if (query.page_token) searchParams.set('page_token', query.page_token);
  if (query.limit) searchParams.set('limit', String(query.limit));
  if (query.hours) searchParams.set('hours', String(query.hours));
  if (query.days) searchParams.set('days', String(query.days));
  if (query.sender) searchParams.set('sender', query.sender);

  const res = await fetch(`${API_URL}/inbox/search?${searchParams.toString()}`, { headers });
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}

export async function getRecentEmails(hours = 4): Promise<EmailMetadata[]> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/inbox/recent?hours=${hours}`, { headers });
  if (!res.ok) throw new Error(`Failed to fetch recent emails: ${res.status}`);
  return res.json();
}

export async function syncRecentEmails(hours = 24): Promise<void> {
  const headers = await getHeaders();
  await fetch(`${API_URL}/inbox/recent?hours=${hours}`, { headers });
}

// ============================================================
// DRAFTS / REPLIES
// ============================================================

export async function createDraft(
  emailId: string,
  instructions?: string
): Promise<DraftCreateResponse> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/replies/drafts`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ email_id: emailId, instructions }),
  });
  if (!res.ok) throw new Error(`Failed to create draft: ${res.status}`);
  return res.json();
}

export async function listDrafts(): Promise<DraftItem[]> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/replies/drafts`, { headers });
  if (!res.ok) throw new Error(`Failed to list drafts: ${res.status}`);
  return res.json();
}

export async function editDraft(
  draftId: string,
  instructions: string,
  currentBody?: string
): Promise<DraftEditResponse> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/replies/drafts/${draftId}/edit`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ instructions, current_body: currentBody }),
  });
  if (!res.ok) throw new Error(`Failed to edit draft: ${res.status}`);
  return res.json();
}

export async function prepareSendDraft(
  draftId: string,
  currentBody?: string
): Promise<PrepareSendResponse> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/replies/drafts/${draftId}/prepare-send`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ current_body: currentBody }),
  });
  if (!res.ok) throw new Error(`Failed to prepare send: ${res.status}`);
  return res.json();
}

export async function executeSendDraft(
  draftId: string,
  approvalId: string
): Promise<Record<string, unknown>> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/replies/drafts/${draftId}/send`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ approval_id: approvalId }),
  });
  if (!res.ok) throw new Error(`Failed to send draft: ${res.status}`);
  return res.json();
}

export async function discardDraft(draftId: string): Promise<void> {
  const headers = await getHeaders();
  await fetch(`${API_URL}/replies/drafts/${draftId}`, {
    method: 'DELETE',
    headers,
  });
}

// ============================================================
// CALENDAR
// ============================================================

export async function extractMeetingDetails(text: string, userTimezone: string) {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/calendar/extract`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ text, user_timezone: userTimezone }),
  });
  if (!res.ok) throw new Error(`Extract meeting failed: ${res.status}`);
  return res.json();
}

export async function checkAvailability(data: {
  preferred_date?: string;
  preferred_time?: string;
  duration_minutes: number;
  participants: string[];
  user_timezone: string;
}) {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/calendar/availability`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Availability check failed: ${res.status}`);
  return res.json();
}

export async function previewCalendarEvent(data: {
  title: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  participants: string[];
  description?: string;
  generate_meet?: boolean;
  source_email_id?: string;
}): Promise<CalendarPreviewResponse> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/calendar/preview`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Preview event failed: ${res.status}`);
  return res.json();
}

export async function confirmCalendarEvent(
  approvalId: string,
  previewId: string
): Promise<Record<string, unknown>> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/calendar/confirm`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ approval_id: approvalId, preview_id: previewId }),
  });
  if (!res.ok) throw new Error(`Confirm event failed: ${res.status}`);
  return res.json();
}

// ============================================================
// DASHBOARD
// ============================================================

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/dashboard/summary`, { headers });
  if (!res.ok) throw new Error(`Dashboard summary failed: ${res.status}`);
  return res.json();
}

// ============================================================
// INTEGRATIONS / GOOGLE
// ============================================================

export async function getGoogleIntegrationStatus(): Promise<GoogleIntegrationStatus> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/integrations/google/status`, { headers });
  if (!res.ok) throw new Error(`Status check failed: ${res.status}`);
  return res.json();
}

export async function connectGoogle(extraScopes?: string): Promise<string> {
  const { getStoredToken } = await import('./auth');
  const token = await getStoredToken();

  const params = new URLSearchParams({ redirect: 'false' });
  if (extraScopes) params.set('scopes', extraScopes);

  const res = await fetch(
    `${API_URL}/integrations/google/connect?${params.toString()}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/json',
      },
    }
  );
  if (!res.ok) throw new Error(`Connect failed: ${res.status}`);
  const data = await res.json();
  return data.url;
}

export async function disconnectGoogle(): Promise<void> {
  const headers = await getHeaders();
  await fetch(`${API_URL}/integrations/google`, {
    method: 'DELETE',
    headers,
  });
}

// ============================================================
// KNOWLEDGE BASE
// ============================================================

export async function listKnowledgeDocuments(): Promise<KnowledgeDocument[]> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/knowledge/documents`, { headers });
  if (!res.ok) throw new Error(`List docs failed: ${res.status}`);
  return res.json();
}

export async function queryKnowledge(
  query: string,
  limit?: number
): Promise<KnowledgeQueryResult[]> {
  const headers = await getFormHeaders();
  const formData = new FormData();
  formData.append('query', query);
  if (limit) formData.append('limit', String(limit));

  const res = await fetch(`${API_URL}/knowledge/query`, {
    method: 'POST',
    headers,
    body: formData,
  });
  if (!res.ok) throw new Error(`Knowledge query failed: ${res.status}`);
  return res.json();
}

// ============================================================
// SETTINGS / USER
// ============================================================

export async function getUserProfile(): Promise<UserProfile> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/settings/profile`, { headers });
  if (!res.ok) throw new Error(`Profile fetch failed: ${res.status}`);
  return res.json();
}

export async function updateUserProfile(
  data: Partial<UserProfile>
): Promise<UserProfile> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/settings/profile`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Profile update failed: ${res.status}`);
  return res.json();
}

export async function getUserPreferences(): Promise<UserPreferences> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/settings/preferences`, { headers });
  if (!res.ok) throw new Error(`Preferences fetch failed: ${res.status}`);
  return res.json();
}

export async function updateUserPreferences(
  data: UserPreferences
): Promise<UserPreferences> {
  const headers = await getFormHeaders();
  const formData = new FormData();
  if (data.timezone) formData.append('timezone', data.timezone);
  if (data.language) formData.append('language', data.language);
  if (data.voice_history_opt_in !== undefined)
    formData.append('voice_history_opt_in', String(data.voice_history_opt_in));

  const res = await fetch(`${API_URL}/settings/preferences`, {
    method: 'PUT',
    headers,
    body: formData,
  });
  if (!res.ok) throw new Error(`Preferences update failed: ${res.status}`);
  return res.json();
}

// ============================================================
// RESEARCH
// ============================================================

export async function runResearch(
  company: string,
  context?: string
): Promise<Record<string, unknown>> {
  const headers = await getFormHeaders();
  const formData = new FormData();
  formData.append('company', company);
  if (context) formData.append('context', context);

  const res = await fetch(`${API_URL}/research/run`, {
    method: 'POST',
    headers,
    body: formData,
  });
  if (!res.ok) throw new Error(`Research failed: ${res.status}`);
  return res.json();
}

// ============================================================
// PLAYBOOKS
// ============================================================

export async function listPlaybooks(): Promise<Playbook[]> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/playbooks`, { headers });
  if (!res.ok) throw new Error(`List playbooks failed: ${res.status}`);
  return res.json();
}

// ============================================================
// VIP CONTACTS
// ============================================================

export async function listVipContacts(): Promise<VIPContact[]> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/vip-contacts`, { headers });
  if (!res.ok) throw new Error(`List VIP contacts failed: ${res.status}`);
  return res.json();
}
```

---

## Phase 5 — WebSocket Client

File: `src/lib/websocket-client.ts`

The backend WebSocket is at `ws://localhost:8000/ws?token=<clerk_session_jwt>` 
(see `apps/api/websocket/__init__.py`).

**Important:** Chrome service workers cannot maintain persistent WebSocket connections. The WebSocket must live in the **side panel** (which has a DOM and stays alive while open). When the side panel closes, the connection drops — reconnect on next open.

```typescript
import { getStoredToken } from './auth';
import type { WsEvent } from './types';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

type EventHandler = (event: WsEvent) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<EventHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // starts at 1s, doubles each attempt
  private shouldReconnect = false;

  async connect(): Promise<void> {
    const token = await getStoredToken();
    if (!token) {
      console.warn('[WS] No token available, cannot connect');
      return;
    }

    this.shouldReconnect = true;
    this.reconnectAttempts = 0;
    this._connect(token);
  }

  private _connect(token: string): void {
    if (this.ws) {
      this.ws.close();
    }

    const url = `${WS_URL}?token=${encodeURIComponent(token)}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('[WS] Connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WsEvent;
        this._emit(data.type, data);
      } catch (err) {
        console.warn('[WS] Failed to parse message:', err);
      }
    };

    this.ws.onclose = (event) => {
      console.log(`[WS] Disconnected (code: ${event.code})`);
      this.ws = null;
      if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
        this.reconnectAttempts++;
        console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
        setTimeout(() => {
          getStoredToken().then((token) => {
            if (token) this._connect(token);
          });
        }, delay);
      }
    };

    this.ws.onerror = (error) => {
      console.error('[WS] Error:', error);
    };
  }

  disconnect(): void {
    this.shouldReconnect = false;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  sendPing(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send('ping');
    }
  }

  on(eventType: string, handler: EventHandler): void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(handler);
  }

  off(eventType: string, handler: EventHandler): void {
    this.listeners.get(eventType)?.delete(handler);
  }

  private _emit(eventType: string, event: WsEvent): void {
    const handlers = this.listeners.get(eventType);
    if (handlers) {
      handlers.forEach((handler) => handler(event));
    }
    // Also emit to wildcard listeners
    const wildcardHandlers = this.listeners.get('*');
    if (wildcardHandlers) {
      wildcardHandlers.forEach((handler) => handler(event));
    }
  }

  get connected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Singleton
export const wsClient = new WebSocketClient();
```

---

## Phase 6 — Zustand Store

File: `src/lib/stores.ts`

One store manages all extension state. Models after the scattered `useState` calls in the web app's `command/page.tsx` but centralized.

```typescript
import { create } from 'zustand';
import type {
  ActiveDraft,
  ActiveCalendarProposal,
  EmailMetadata,
  TranscriptEntry,
  AgentResponse,
} from './types';
import { sendTextCommand } from './api-client';
import { wsClient } from './websocket-client';
import { getStoredToken, getStoredUserInfo, clearStoredAuth } from './auth';

interface ExtensionState {
  // Auth
  isAuthenticated: boolean;
  authEmail: string | null;
  authUserId: string | null;
  isAuthLoading: boolean;

  // Session
  sessionId: string; // persistent UUID, generated once on first launch
  transcript: TranscriptEntry[];
  isCommandLoading: boolean;

  // Active agent results (side panel cards)
  activeDraft: ActiveDraft | null;
  activeProposal: ActiveCalendarProposal | null;
  queryResults: EmailMetadata[];

  // Voice
  isListening: boolean;
  isSpeaking: boolean;

  // WebSocket
  wsConnected: boolean;

  // Badge
  unreadCount: number;

  // Actions
  initAuth: () => Promise<void>;
  setAuthenticated: (token: string, userId: string, email: string) => void;
  logout: () => Promise<void>;

  sendCommand: (text: string) => Promise<void>;
  setTranscript: (entries: TranscriptEntry[]) => void;
  addTranscriptEntry: (entry: TranscriptEntry) => void;
  clearTranscript: () => void;

  setActiveDraft: (draft: ActiveDraft | null) => void;
  setActiveProposal: (proposal: ActiveCalendarProposal | null) => void;
  setQueryResults: (results: EmailMetadata[]) => void;
  setListening: (v: boolean) => void;
  setSpeaking: (v: boolean) => void;
  setWsConnected: (v: boolean) => void;
  setUnreadCount: (count: number) => void;
}

// Generate or retrieve a persistent session_id
function getSessionId(): string {
  const key = 'aether_session_id';
  const stored = localStorage.getItem(key);
  if (stored) return stored;
  const id = crypto.randomUUID();
  localStorage.setItem(key, id);
  return id;
}

export const useStore = create<ExtensionState>((set, get) => ({
  // Initial state
  isAuthenticated: false,
  authEmail: null,
  authUserId: null,
  isAuthLoading: true,
  sessionId: getSessionId(),
  transcript: [],
  isCommandLoading: false,
  activeDraft: null,
  activeProposal: null,
  queryResults: [],
  isListening: false,
  isSpeaking: false,
  wsConnected: false,
  unreadCount: 0,

  // Auth actions
  initAuth: async () => {
    const token = await getStoredToken();
    const userInfo = await getStoredUserInfo();
    if (token && userInfo) {
      set({
        isAuthenticated: true,
        authEmail: userInfo.email,
        authUserId: userInfo.userId,
        isAuthLoading: false,
      });
    } else {
      set({ isAuthLoading: false });
    }
  },

  setAuthenticated: (token, userId, email) => {
    set({
      isAuthenticated: true,
      authEmail: email,
      authUserId: userId,
      isAuthLoading: false,
    });
  },

  logout: async () => {
    await clearStoredAuth();
    set({
      isAuthenticated: false,
      authEmail: null,
      authUserId: null,
      transcript: [],
      activeDraft: null,
      activeProposal: null,
      queryResults: [],
    });
  },

  // Command actions
  sendCommand: async (text: string) => {
    const { sessionId, isCommandLoading } = get();
    if (isCommandLoading || !text.trim()) return;

    const userEntry: TranscriptEntry = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    set((state) => ({
      transcript: [...state.transcript, userEntry],
      isCommandLoading: true,
    }));

    try {
      const data = await sendTextCommand(text, sessionId);
      const respObj: AgentResponse = data.response;

      // Build assistant response
      let responseText = 'Task completed successfully.';
      if (respObj.result?.message) responseText = respObj.result.message;
      else if (respObj.status === 'clarification_needed') {
        responseText = respObj.result?.clarification || 'Could you please clarify?';
      } else if (respObj.result?.summary) responseText = respObj.result.summary;
      else if (respObj.result?.answer) responseText = respObj.result.answer;
      else if (typeof respObj.result === 'string') responseText = respObj.result;

      // Extract query results
      const items: EmailMetadata[] =
        respObj.result?.items || respObj.context_updates?.last_search_results || [];
      if (items.length > 0) {
        set({ queryResults: items });
      }

      // Extract draft
      const draftId =
        respObj.result?.draft_id || respObj.context_updates?.active_draft_id;
      const draftBody =
        respObj.result?.draft_body || respObj.context_updates?.active_draft_body;
      if (draftId && draftBody) {
        set({
          activeDraft: {
            draft_id: draftId,
            draft_body: draftBody,
            has_gaps:
              respObj.result?.has_gaps ??
              respObj.context_updates?.has_gaps ??
              false,
            gap_notes:
              respObj.result?.gap_notes ??
              respObj.context_updates?.gap_notes ??
              [],
            recipient:
              respObj.result?.target_email?.sender || items[0]?.sender || 'Recipient',
            subject:
              respObj.result?.target_email?.subject || items[0]?.subject || 'Reply Draft',
          },
        });
      }

      // Extract calendar proposal
      const previewId =
        respObj.result?.preview_id ||
        respObj.context_updates?.active_calendar_preview_id;
      const approvalId =
        respObj.result?.approval_id ||
        respObj.context_updates?.active_calendar_approval_id;
      if (previewId && respObj.result?.start && respObj.result?.end) {
        set({
          activeProposal: {
            preview_id: previewId,
            approval_id: approvalId,
            title: respObj.result?.title || 'Meeting Proposal',
            start: respObj.result.start,
            end: respObj.result.end,
            duration_minutes: respObj.result?.duration_minutes || 60,
            attendees: respObj.result?.participants || [],
            meet_link: respObj.result?.meet_link,
            double_booking_warnings: respObj.result?.double_booking_warnings,
          },
        });
      }

      const assistantEntry: TranscriptEntry = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: responseText,
        agent_used: respObj.agent || 'Supervisor',
        timestamp: new Date().toISOString(),
        draft_id: draftId,
        draft_body: draftBody,
        requires_approval: respObj.requires_approval,
      };

      set((state) => ({
        transcript: [...state.transcript, assistantEntry],
        isCommandLoading: false,
      }));
    } catch (err: unknown) {
      const errorEntry: TranscriptEntry = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `Error: ${err instanceof Error ? err.message : 'Failed to execute command'}`,
        agent_used: 'Supervisor',
        timestamp: new Date().toISOString(),
      };
      set((state) => ({
        transcript: [...state.transcript, errorEntry],
        isCommandLoading: false,
      }));
    }
  },

  setTranscript: (entries) => set({ transcript: entries }),
  addTranscriptEntry: (entry) =>
    set((state) => ({ transcript: [...state.transcript, entry] })),
  clearTranscript: () => set({ transcript: [] }),

  setActiveDraft: (draft) => set({ activeDraft: draft }),
  setActiveProposal: (proposal) => set({ activeProposal: proposal }),
  setQueryResults: (results) => set({ queryResults: results }),
  setListening: (v) => set({ isListening: v }),
  setSpeaking: (v) => set({ isSpeaking: v }),
  setWsConnected: (v) => set({ wsConnected: v }),
  setUnreadCount: (count) => set({ unreadCount: count }),
}));
```

---

## Phase 7 — Side Panel UI

### 7.1 Entry Point

File: `src/sidepanel/main.tsx`

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/globals.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

### 7.2 Root Component

File: `src/sidepanel/App.tsx`

```typescript
import { useEffect } from 'react';
import { useStore } from '../lib/stores';
import { wsClient } from '../lib/websocket-client';
import { AuthGate } from './components/AuthGate';
import { Header } from './components/Header';
import { Transcript } from './components/Transcript';
import { CommandBar } from './components/CommandBar';
import { DraftCard } from './components/DraftCard';
import { CalendarCard } from './components/CalendarCard';
import { Avatar } from './components/Avatar';

export default function App() {
  const {
    isAuthenticated,
    isAuthLoading,
    initAuth,
    wsConnected,
    setWsConnected,
    activeDraft,
    activeProposal,
  } = useStore();

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  useEffect(() => {
    if (isAuthenticated) {
      wsClient.on('connected', () => setWsConnected(true));
      wsClient.on('*', (event) => console.log('[WS Event]', event));
      wsClient.connect();

      return () => {
        wsClient.disconnect();
        setWsConnected(false);
      };
    }
  }, [isAuthenticated, setWsConnected]);

  if (isAuthLoading) {
    return (
      <div className="flex h-screen items-center justify-center text-sm text-muted-foreground">
        Loading...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AuthGate />;
  }

  return (
    <div className="flex h-screen flex-col bg-background text-foreground">
      <Header wsConnected={wsConnected} />
      
      <div className="flex-1 overflow-y-auto space-y-3 p-3">
        {/* Active Draft Card */}
        {activeDraft && <DraftCard draft={activeDraft} />}

        {/* Active Calendar Proposal Card */}
        {activeProposal && <CalendarCard proposal={activeProposal} />}

        {/* Conversation Transcript */}
        <Transcript />
      </div>

      <CommandBar />
    </div>
  );
}
```

### 7.3 AuthGate Component

File: `src/sidepanel/components/AuthGate.tsx`

```typescript
import { useState } from 'react';
import { signInWithClerk } from '../../lib/auth';
import { useStore } from '../../lib/stores';
import { Sparkles } from 'lucide-react';

export function AuthGate() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const setAuthenticated = useStore((s) => s.setAuthenticated);

  const handleSignIn = async () => {
    setLoading(true);
    setError(null);
    try {
      const authState = await signInWithClerk();
      setAuthenticated(authState.token!, authState.userId!, authState.email!);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Sign in failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen flex-col items-center justify-center gap-4 p-6 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
        <Sparkles className="h-8 w-8" />
      </div>
      <h1 className="text-xl font-semibold">Aether</h1>
      <p className="text-sm text-muted-foreground">
        AI Chief of Staff for your inbox
      </p>
      <button
        onClick={handleSignIn}
        disabled={loading}
        className="mt-2 rounded-lg bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
      >
        {loading ? 'Signing in...' : 'Sign in with Clerk'}
      </button>
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  );
}
```

### 7.4 Header Component

File: `src/sidepanel/components/Header.tsx`

```typescript
import { useStore } from '../../lib/stores';
import { Sparkles, Wifi, WifiOff, LogOut } from 'lucide-react';

interface HeaderProps {
  wsConnected: boolean;
}

export function Header({ wsConnected }: HeaderProps) {
  const { authEmail, logout } = useStore();

  return (
    <header className="flex items-center justify-between border-b border-border px-3 py-2">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-primary" />
        <span className="text-sm font-semibold">Aether</span>
        {wsConnected ? (
          <Wifi className="h-3 w-3 text-emerald-500" />
        ) : (
          <WifiOff className="h-3 w-3 text-muted-foreground" />
        )}
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground truncate max-w-[120px]">
          {authEmail}
        </span>
        <button
          onClick={logout}
          className="rounded p-1 hover:bg-muted text-muted-foreground hover:text-foreground"
          title="Sign out"
        >
          <LogOut className="h-3.5 w-3.5" />
        </button>
      </div>
    </header>
  );
}
```

### 7.5 Avatar Component

File: `src/sidepanel/components/Avatar.tsx`

Mirrors the web app's orb/avatar that shows listening/speaking/idle state.

```typescript
import { useStore } from '../../lib/stores';
import { Sparkles } from 'lucide-react';

export function Avatar() {
  const { isListening, isSpeaking } = useStore();

  const stateClass = isSpeaking
    ? 'animate-pulse shadow-[0_0_30px_var(--color-primary)]'
    : isListening
    ? 'animate-pulse'
    : '';

  const label = isSpeaking
    ? 'Speaking...'
    : isListening
    ? 'Listening...'
    : 'Idle';

  return (
    <div className="flex flex-col items-center gap-2 py-4">
      <div
        className={`relative h-20 w-20 rounded-full bg-gradient-to-br from-primary via-primary/70 to-accent transition-all ${stateClass}`}
      >
        <div className="absolute inset-0 flex items-center justify-center">
          <Sparkles className="h-6 w-6 text-primary-foreground" />
        </div>
      </div>
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
    </div>
  );
}
```

### 7.6 Transcript Component

File: `src/sidepanel/components/Transcript.tsx`

```typescript
import { useEffect, useRef } from 'react';
import { useStore } from '../../lib/stores';
import type { TranscriptEntry } from '../../lib/types';

export function Transcript() {
  const transcript = useStore((s) => s.transcript);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript]);

  if (transcript.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center text-xs text-muted-foreground">
        <p>Type a command below to get started.</p>
        <p className="mt-1">e.g., "show me my unread emails"</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {transcript.map((entry) => (
        <TranscriptBubble key={entry.id} entry={entry} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}

function TranscriptBubble({ entry }: { entry: TranscriptEntry }) {
  const isUser = entry.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
          isUser
            ? 'bg-secondary text-secondary-foreground'
            : 'border border-primary/30 bg-primary/5'
        }`}
      >
        {!isUser && (
          <div className="mb-1 flex items-center gap-1.5">
            <span className="text-[10px] font-medium text-muted-foreground uppercase">
              Aether
            </span>
            {entry.agent_used && (
              <span className="rounded border border-border px-1 py-0 text-[9px] text-muted-foreground">
                {entry.agent_used}
              </span>
            )}
          </div>
        )}
        <p className="whitespace-pre-wrap leading-relaxed">{entry.content}</p>
      </div>
    </div>
  );
}
```

### 7.7 CommandBar Component

File: `src/sidepanel/components/CommandBar.tsx`

```typescript
import { useState } from 'react';
import { useStore } from '../../lib/stores';
import { VoiceButton } from './VoiceButton';
import { Send } from 'lucide-react';

export function CommandBar() {
  const [input, setInput] = useState('');
  const { sendCommand, isCommandLoading } = useStore();

  const handleSubmit = () => {
    if (!input.trim() || isCommandLoading) return;
    sendCommand(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-border p-2">
      <div className="flex items-center gap-2">
        <VoiceButton />
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isCommandLoading}
          placeholder="Type a command..."
          className="flex-1 rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary disabled:opacity-50"
        />
        <button
          onClick={handleSubmit}
          disabled={isCommandLoading || !input.trim()}
          className="rounded-lg bg-primary p-2 text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          <Send className={`h-4 w-4 ${isCommandLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>
    </div>
  );
}
```

### 7.8 VoiceButton Component

File: `src/sidepanel/components/VoiceButton.tsx`

```typescript
import { useRef, useState } from 'react';
import { useStore } from '../../lib/stores';
import { AudioRecorder } from '../../utils/audio';
import { sendVoiceCommand } from '../../lib/api-client';
import { Mic, MicOff } from 'lucide-react';

export function VoiceButton() {
  const { isListening, setListening, sessionId, addTranscriptEntry } = useStore();
  const recorderRef = useRef<AudioRecorder | null>(null);

  const handleMouseDown = async () => {
    try {
      const recorder = new AudioRecorder();
      await recorder.startRecording();
      recorderRef.current = recorder;
      setListening(true);
    } catch (err) {
      console.error('Failed to start recording:', err);
    }
  };

  const handleMouseUp = async () => {
    const recorder = recorderRef.current;
    if (!recorder) return;

    setListening(false);
    recorderRef.current = null;

    try {
      const blob = await recorder.stopRecording();
      const data = await sendVoiceCommand(blob, sessionId);

      addTranscriptEntry({
        id: crypto.randomUUID(),
        role: 'user',
        content: `🎤 ${data.transcript}`,
        timestamp: new Date().toISOString(),
      });

      addTranscriptEntry({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.response.result?.message || 'Voice command processed.',
        agent_used: data.response.agent,
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      console.error('Voice command failed:', err);
    }
  };

  return (
    <button
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={() => {
        if (recorderRef.current) handleMouseUp();
      }}
      className={`rounded-lg p-2 transition-colors ${
        isListening
          ? 'bg-destructive text-destructive-foreground animate-pulse'
          : 'bg-muted text-muted-foreground hover:bg-muted/80'
      }`}
      title={isListening ? 'Release to send' : 'Hold to record voice'}
    >
      {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
    </button>
  );
}
```

### 7.9 DraftCard Component

File: `src/sidepanel/components/DraftCard.tsx`

```typescript
import { useState } from 'react';
import type { ActiveDraft } from '../../lib/types';
import { prepareSendDraft, executeSendDraft } from '../../lib/api-client';
import { useStore } from '../../lib/stores';
import { Sparkles, CheckCircle2, AlertTriangle, Trash2 } from 'lucide-react';

interface DraftCardProps {
  draft: ActiveDraft;
}

export function DraftCard({ draft }: DraftCardProps) {
  const [sending, setSending] = useState(false);
  const setActiveDraft = useStore((s) => s.setActiveDraft);

  const handleApproveAndSend = async () => {
    setSending(true);
    try {
      const prep = await prepareSendDraft(draft.draft_id, draft.draft_body);
      await executeSendDraft(draft.draft_id, prep.approval_id);
      setActiveDraft(null);
      alert('Draft approved and sent!');
    } catch (err: unknown) {
      alert(`Failed to send: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="rounded-lg border border-primary/60 bg-card p-3 shadow-sm space-y-2">
      <div className="flex items-center justify-between border-b pb-1.5">
        <div className="flex items-center gap-1.5">
          <Sparkles className="h-3.5 w-3.5 text-primary" />
          <span className="text-[10px] font-semibold text-primary uppercase tracking-wider">
            AI Reply Draft
          </span>
        </div>
        <span className="rounded border border-amber-500/50 px-1.5 py-0 text-[9px] text-amber-600">
          Awaiting Approval
        </span>
      </div>

      {draft.recipient && (
        <div className="text-xs">
          <span className="font-medium text-muted-foreground">To:</span>{' '}
          <span className="font-medium">{draft.recipient}</span>
        </div>
      )}

      {draft.has_gaps && (
        <div className="rounded border border-amber-500/40 bg-amber-500/10 p-2 text-xs text-amber-700 space-y-0.5">
          <div className="flex items-center gap-1 font-semibold">
            <AlertTriangle className="h-3 w-3" />
            <span>Knowledge Gap</span>
          </div>
          {draft.gap_notes?.map((note, i) => (
            <p key={i} className="text-[10px] opacity-90">{note}</p>
          ))}
        </div>
      )}

      <div className="max-h-32 overflow-y-auto rounded border bg-muted/40 p-2 text-xs whitespace-pre-wrap leading-relaxed">
        {draft.draft_body}
      </div>

      <div className="flex items-center gap-2 pt-0.5">
        <button
          onClick={handleApproveAndSend}
          disabled={sending}
          className="flex-1 rounded bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {sending ? 'Sending...' : 'Approve & Send'}
        </button>
        <button
          onClick={() => setActiveDraft(null)}
          className="rounded p-1.5 text-muted-foreground hover:text-destructive"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
```

### 7.10 CalendarCard Component

File: `src/sidepanel/components/CalendarCard.tsx`

```typescript
import { useState } from 'react';
import type { ActiveCalendarProposal } from '../../lib/types';
import { confirmCalendarEvent } from '../../lib/api-client';
import { useStore } from '../../lib/stores';
import { CalendarIcon, CheckCircle2, Video, Trash2 } from 'lucide-react';

interface CalendarCardProps {
  proposal: ActiveCalendarProposal;
}

export function CalendarCard({ proposal }: CalendarCardProps) {
  const [confirming, setConfirming] = useState(false);
  const setActiveProposal = useStore((s) => s.setActiveProposal);

  const handleConfirm = async () => {
    setConfirming(true);
    try {
      await confirmCalendarEvent(proposal.approval_id || proposal.preview_id, proposal.preview_id);
      setActiveProposal(null);
      alert('Calendar event confirmed!');
    } catch (err: unknown) {
      alert(`Failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setConfirming(false);
    }
  };

  return (
    <div className="rounded-lg border border-emerald-500/60 bg-card p-3 shadow-sm space-y-2">
      <div className="flex items-center justify-between border-b pb-1.5">
        <div className="flex items-center gap-1.5">
          <CalendarIcon className="h-3.5 w-3.5 text-emerald-500" />
          <span className="text-[10px] font-semibold text-emerald-600 uppercase tracking-wider">
            Calendar Proposal
          </span>
        </div>
        <span className="rounded border border-emerald-500/50 px-1.5 py-0 text-[9px] text-emerald-600">
          Awaiting Approval
        </span>
      </div>

      <div className="space-y-1 text-xs">
        <div>
          <span className="font-medium text-muted-foreground">Title:</span>{' '}
          <span className="font-medium">{proposal.title}</span>
        </div>
        <div>
          <span className="font-medium text-muted-foreground">Time:</span>{' '}
          <span className="font-medium">
            {new Date(proposal.start).toLocaleString([], {
              dateStyle: 'medium',
              timeStyle: 'short',
            })}{' '}
            –{' '}
            {new Date(proposal.end).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>
        {proposal.attendees.length > 0 && (
          <div>
            <span className="font-medium text-muted-foreground">Attendees:</span>{' '}
            <span className="font-medium">{proposal.attendees.join(', ')}</span>
          </div>
        )}
        {proposal.meet_link && (
          <div className="flex items-center gap-1 text-emerald-600">
            <Video className="h-3 w-3" />
            <span className="text-[10px] truncate">{proposal.meet_link}</span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={handleConfirm}
          disabled={confirming}
          className="flex-1 rounded bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {confirming ? 'Creating...' : 'Approve & Create'}
        </button>
        <button
          onClick={() => setActiveProposal(null)}
          className="rounded p-1.5 text-muted-foreground hover:text-destructive"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
```

### 7.11 Styles

File: `src/sidepanel/styles/globals.css`

```css
/* Minimal reset + Aether design tokens */
:root {
  --background: #050505;
  --foreground: #f9fafb;
  --primary: #3b82f6;
  --primary-foreground: #ffffff;
  --secondary: #1f2937;
  --secondary-foreground: #f9fafb;
  --muted: #1f2937;
  --muted-foreground: #9ca3af;
  --accent: #10b981;
  --accent-foreground: #ffffff;
  --destructive: #ef4444;
  --destructive-foreground: #ffffff;
  --border: #1f2937;
  --input: #1f2937;
  --ring: #3b82f6;
  --radius: 0.5rem;
  --card: #0f0f10;
  --card-foreground: #f9fafb;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #root {
  height: 100%;
  width: 100%;
  overflow: hidden;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--background);
  color: var(--foreground);
  font-size: 14px;
  -webkit-font-smoothing: antialiased;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 4px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: var(--muted);
  border-radius: 2px;
}

/* Animations */
@keyframes pulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.05); }
}

.animate-pulse {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
```

---

## Phase 8 — Background Service Worker

File: `src/background/service-worker.ts`

Full service worker with:
1. Side panel toggle on extension icon click
2. Auth state management
3. Badge count polling via `chrome.alarms`

```typescript
import { getStoredToken } from '../lib/auth';

// ============================================================
// SIDE PANEL — Open on extension icon click
// ============================================================

chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch(console.error);

// ============================================================
// AUTH STATE — Keep in memory for badge polling
// ============================================================

let currentToken: string | null = null;

async function initAuth() {
  currentToken = await getStoredToken();
}

initAuth();

chrome.storage.onChanged.addListener((changes) => {
  if (changes.clerk_session_token) {
    currentToken = changes.clerk_session_token.newValue || null;
    // Update badge after auth change
    if (currentToken) {
      updateBadge();
    } else {
      chrome.action.setBadgeText({ text: '' });
    }
  }
});

// ============================================================
// ALARMS — Periodic polling for badge count
// ============================================================

// Create alarm on install
chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create('poll-dashboard', { periodInMinutes: 5 });
});

// Listen for alarm
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'poll-dashboard' && currentToken) {
    updateBadge();
  }
});

async function updateBadge() {
  if (!currentToken) return;

  try {
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const res = await fetch(`${API_URL}/dashboard/summary`, {
      headers: { Authorization: `Bearer ${currentToken}` },
    });

    if (res.ok) {
      const data = await res.json();
      const count = (data.high_priority || 0) + (data.pending_approvals || 0);

      chrome.action.setBadgeText({
        text: count > 0 ? String(count) : '',
      });
      chrome.action.setBadgeBackgroundColor({
        color: count > 0 ? '#ef4444' : '#22c55e',
      });
    }
  } catch (err) {
    console.warn('[Badge] Poll failed:', err);
  }
}

// ============================================================
// MESSAGE RELAY — Pass auth between contexts
// ============================================================

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'AUTH_UPDATED') {
    currentToken = message.token;
    sendResponse({ success: true });
  }
  if (message.type === 'GET_TOKEN') {
    sendResponse({ token: currentToken });
  }
  if (message.type === 'OPEN_SIDE_PANEL') {
    chrome.sidePanel.open({ tabId: sender.tab?.id });
    sendResponse({ success: true });
  }
  return true; // async
});
```

---

## Phase 9 — Voice Input Utility

File: `src/utils/audio.ts`

```typescript
export class AudioRecorder {
  private mediaRecorder: MediaRecorder | null = null;
  private chunks: Blob[] = [];
  private stream: MediaStream | null = null;

  async startRecording(): Promise<void> {
    // Request mic permission — this triggers Chrome's permission prompt
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: 48000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
      },
    });

    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm';

    this.mediaRecorder = new MediaRecorder(this.stream, { mimeType });
    this.chunks = [];

    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        this.chunks.push(event.data);
      }
    };

    this.mediaRecorder.start(250); // collect data every 250ms
  }

  stopRecording(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder) {
        reject(new Error('No active recording'));
        return;
      }

      this.mediaRecorder.onstop = () => {
        const blob = new Blob(this.chunks, { type: this.mediaRecorder!.mimeType });
        this.chunks = [];

        // Stop all tracks to release the microphone
        if (this.stream) {
          this.stream.getTracks().forEach((track) => track.stop());
          this.stream = null;
        }

        resolve(blob);
      };

      this.mediaRecorder.stop();
    });
  }
}
```

---

## Phase 10 — Cross-Device Session Sharing

### 10.1 How it works

The backend's `POST /command` uses a `session_id` that is **client-generated**. The web app's command page generates it with `crypto.randomUUID()` and stores it in memory. The extension's store generates it with the same approach and persists it in `localStorage`.

```
Web App:  session_id = "abc-123"  →  Backend stores context under "abc-123"
Extension: session_id = "xyz-789" →  Backend stores context under "xyz-789"
```

**They are independent conversation threads** — and this is correct. You don't want voice commands in the extension to confuse the context of the web app's command center.

**What IS shared between them:** All user data. Because both clients authenticate as the same user (same Clerk token → same `user_id`), they share:
- The same inbox (emails fetched from Gmail via `google_integrations`)
- The same drafts (visible in `GET /replies/drafts` from either client)
- The same calendar proposals (visible in `GET /calendar/meetings`)
- The same knowledge base, playbooks, VIP contacts, settings

### 10.2 Implementation

The store already generates a persistent `sessionId`:

```typescript
function getSessionId(): string {
  const key = 'aether_session_id';
  const stored = localStorage.getItem(key);
  if (stored) return stored;
  const id = crypto.randomUUID();
  localStorage.setItem(key, id);
  return id;
}
```

This means the extension's conversation context persists across side panel opens/closes. No additional work needed.

---

## Phase 11 — Build & Package

### 11.1 Build script

```bash
cd apps/extension
npm run build   # runs vite build → outputs to dist/
```

### 11.2 `package.json` scripts

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint src/"
  }
}
```

### 11.3 Load in Chrome

1. Open `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `apps/extension/dist/`
5. Pin the extension to the toolbar
6. Click the icon → side panel opens

### 11.4 Environment variables

Create `.env` in `apps/extension/`:

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxx
VITE_CLERK_FRONTEND_API=your-app.clerk.accounts.dev
```

---

## Phase 12 — Verification Checklist

### 12.1 Auth Flow

| Test | Expected |
|------|----------|
| Click "Sign in with Clerk" | Popup opens to Clerk sign-in page |
| Sign in with any email | Popup closes, extension shows authenticated UI |
| Reload extension | Token persists, auto-authenticated |
| Sign out | Token cleared, AuthGate shown, badge cleared |

### 12.2 Command Flow

| Test | Expected |
|------|----------|
| Type "show me my unread emails" | POST to /command, agent response shown in transcript |
| Type "draft reply to [email]" | DraftCard appears with "Approve & Send" button |
| Click "Approve & Send" | prepare-send + send chain executes, email sent via Gmail |
| Type "schedule meeting" | CalendarCard appears with time/attendees |
| Click "Approve & Create" | Calendar event confirmed, alert shown |

### 12.3 Voice Flow

| Test | Expected |
|------|----------|
| Hold mic button | Permission prompt (first time), recording indicator |
| Release mic button | Audio blob sent to /command/voice, transcript + response shown |

### 12.4 WebSocket

| Test | Expected |
|------|----------|
| Open side panel | "connected" event logged, green Wifi icon |
| Receive new email (backend simulated) | Event received in console |

### 12.5 Badge

| Test | Expected |
|------|----------|
| High-priority emails exist | Red badge count on extension icon |
| No high-priority emails | No badge text |
| Wait 5 minutes | Badge refreshes via alarm |

### 12.6 Cross-Device Data Sharing

| Test | Expected |
|------|----------|
| Create draft on web app | Open extension → /replies shows the same draft |
| Send email from extension | Draft disappears from web app's /replies too |
| Sync inbox from web | Extension's /inbox shows the same emails |

### 12.7 Google Integration (Settings)

| Test | Expected |
|------|----------|
| Open Settings in extension | Shows Google connection status from /integrations/google/status |
| Click "Connect Google" | Opens Google OAuth consent screen in popup |
| Complete OAuth | Status updates to connected |
| Disconnect | Status updates to disconnected, non-Gmail features still work |

---

## Phase 13 — Future Enhancements

After the MVP extension is working, consider:

1. **Content Script** — Inject a small widget into Gmail's web UI that communicates with the extension
2. **Keyboard Shortcuts** — `Ctrl+Shift+A` to open the side panel
3. **Desktop Notifications** — `chrome.notifications` for high-priority emails
4. **Offline Mode** — Cache recent emails and commands in `chrome.storage.local`
5. **Multiple Google Accounts** — Connect multiple inboxes and switch between them
6. **Context Sharing** — Optionally share `session_id` between web and extension via a QR code or link

---

## Appendix A — Complete API Reference

Every API endpoint exposed by `apps/api/` that the extension consumes:

### Command Center (`/command`)
| Method | Path | Auth | Request | Response |
|--------|------|------|---------|----------|
| POST | `/command` | Yes (Bearer) | `FormData`: `command`, `session_id?` | `{ session_id, response: AgentResponse }` |
| POST | `/command/voice` | Yes (Bearer) | `FormData`: `audio` (file), `session_id?` | `{ session_id, transcript, response: AgentResponse }` |

### Inbox (`/inbox`)
| Method | Path | Auth | Query Params | Response |
|--------|------|------|-------------|----------|
| GET | `/inbox/emails` | Yes | `priority?`, `category?`, `sender?`, `hours?`, `days?`, `limit`(1-100), `offset` | `EmailMetadata[]` |
| GET | `/inbox/emails/{email_id}` | Yes | — | `EmailMetadata` |
| GET | `/inbox/search` | Yes | `q` (required), `page_token?`, `limit`, `hours?`, `days?`, `sender?` | `EmailMetadata[]` |
| GET | `/inbox/recent` | Yes | `hours`(1-168, default 4) | `EmailMetadata[]` |

### Drafts / Replies (`/replies`)
| Method | Path | Auth | Request Body | Response |
|--------|------|------|-------------|----------|
| POST | `/replies/drafts` | Yes | `{ email_id, instructions? }` | Draft create result |
| GET | `/replies/drafts` | Yes | — | `DraftItem[]` |
| PUT | `/replies/drafts/{id}` | Yes | `{ current_body }` | `{ status, draft_id, body }` |
| POST | `/replies/drafts/{id}/edit` | Yes | `{ instructions, current_body? }` | Edit result |
| POST | `/replies/drafts/{id}/prepare-send` | Yes | `{ current_body? }` | Prep result with `approval_id` |
| POST | `/replies/drafts/{id}/send` | Yes | `{ approval_id }` | Send result |
| DELETE | `/replies/drafts/{id}` | Yes | — | `{ status: "discarded" }` |

### Calendar (`/calendar`)
| Method | Path | Auth | Request Body | Response |
|--------|------|------|-------------|----------|
| POST | `/calendar/extract` | Yes | `{ text, user_timezone }` | Extracted `MeetingDetails` |
| POST | `/calendar/availability` | Yes | `{ preferred_date?, time?, duration_minutes, participants[], user_timezone }` | `{ free_slots[], warnings[] }` |
| POST | `/calendar/preview` | Yes | `{ title, start_time, end_time, duration_minutes, participants[], description?, generate_meet?, source_email_id? }` | Preview with `approval_id` |
| POST | `/calendar/confirm` | Yes | `{ approval_id, preview_id }` | Confirmed event |
| GET | `/calendar/meetings` | Yes | — | `MeetingResponse[]` |

### Dashboard (`/dashboard`)
| Method | Path | Auth | Response |
|--------|------|------|----------|
| GET | `/dashboard/summary` | Yes | `{ total_emails, high_priority, unread, recent_meetings, pending_approvals }` |

### Integrations (`/integrations`)
| Method | Path | Auth | Response |
|--------|------|------|----------|
| GET | `/integrations/google/connect` | Yes | `{ url, state }` (with `redirect=false`) or 307 redirect |
| GET | `/integrations/google/callback` | No (OAuth) | 302 redirect to frontend |
| GET | `/integrations/google/status` | Yes | `{ connected, scopes[], is_expired?, revoked? }` |
| DELETE | `/integrations/google` | Yes | `{ status: "disconnected" }` |

### Knowledge (`/knowledge`)
| Method | Path | Auth | Request | Response |
|--------|------|------|---------|----------|
| GET | `/knowledge/documents` | Yes | — | `KnowledgeDocument[]` |
| POST | `/knowledge/query` | Yes | `FormData`: `query`, `limit?`, `org_id?` | `{ score, payload }[]` |

### Settings (`/settings`)
| Method | Path | Auth | Response |
|--------|------|------|----------|
| GET | `/settings/profile` | Yes | `UserProfile` |
| PUT | `/settings/profile` | Yes | Updated `UserProfile` |
| GET | `/settings/preferences` | Yes | `{ timezone, language, plan_tier, voice_history_opt_in }` |
| PUT | `/settings/preferences` | Yes | Updated preferences |

### Research (`/research`)
| Method | Path | Auth | Request | Response |
|--------|------|------|---------|----------|
| POST | `/research/run` | Yes | `FormData`: `company`, `context?` | Research result |

### Playbooks (`/playbooks`)
| Method | Path | Auth | Response |
|--------|------|------|----------|
| GET | `/playbooks` | Yes | `Playbook[]` |
| GET | `/playbooks/{id}` | Yes | `Playbook` |
| POST | `/playbooks` | Yes | Created `Playbook` |
| PUT | `/playbooks/{id}` | Yes | Updated `Playbook` |
| DELETE | `/playbooks/{id}` | Yes | `{ detail: "Playbook deleted" }` |

### VIP Contacts (`/vip-contacts`)
| Method | Path | Auth | Response |
|--------|------|------|----------|
| GET | `/vip-contacts` | Yes | `VIPContact[]` |
| POST | `/vip-contacts` | Yes | Created `VIPContact` |
| PUT | `/vip-contacts/{id}` | Yes | Updated `VIPContact` |
| DELETE | `/vip-contacts/{id}` | Yes | `{ detail: "VIP contact deleted" }` |

### WebSocket (`/ws`)
| Protocol | Path | Auth | Description |
|----------|------|------|-------------|
| WS | `/ws?token=<clerk_jwt>` | Yes (query param) | Real-time events |

### Agent Response Envelope

All commands return this structure (from `schemas/agent_response_schema.py`):

```typescript
{
  "agent": "string",               // Agent name
  "status": "completed"            //  | "waiting_for_user" | "error" | "clarification_needed"
  "result": {                      // Agent-specific payload
    "message"?: string,            //  Human-readable response
    "summary"?: string,            //  AI summary
    "answer"?: string,             //  Knowledge answer
    "items"?: EmailMetadata[],     //  Search query results
    "draft_id"?: string,           //  Draft created
    "draft_body"?: string,         //  Draft body text
    "preview_id"?: string,         //  Calendar preview
    "approval_id"?: string,        //  Approval required
    "start"?: string,              //  Meeting start (ISO)
    "end"?: string,                //  Meeting end (ISO)
    "title"?: string,              //  Meeting title
    "participants"?: string[],     //  Meeting attendees
    "meet_link"?: string,          //  Google Meet link
    "has_gaps"?: boolean,          //  Knowledge gaps
    "gap_notes"?: string[],        //  Gap details
    "clarification"?: string,      //  Clarification question
    "double_booking_warnings"?: [] //  Calendar conflicts
  },
  "context_updates": {             // Updated conversation state
    "active_draft_id"?: string,
    "active_draft_body"?: string,
    "active_calendar_preview_id"?: string,
    "active_calendar_approval_id"?: string,
    "last_search_results"?: EmailMetadata[],
    "has_gaps"?: boolean,
    "gap_notes"?: string[]
  },
  "requires_approval": false       // true for send/schedule/pay actions
}
```

---

## Appendix B — Environment Variables

```bash
# Backend URL (must match the running FastAPI server)
VITE_API_URL=http://localhost:8000

# WebSocket URL (must match the running FastAPI server)
VITE_WS_URL=ws://localhost:8000/ws

# Clerk — get these from your Clerk Dashboard
VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxx
VITE_CLERK_FRONTEND_API=your-app.clerk.accounts.dev
```

---

## Appendix C — Key Backend Files to Reference

When debugging or adding features, reference these backend files:

| File | What it defines |
|------|----------------|
| `apps/api/main.py` | Route mounts, CORS, middleware, health check |
| `apps/api/core/deps.py` | `get_current_user()` — how auth works |
| `apps/api/core/security.py` | JWT verification, token encryption, OAuth helpers |
| `apps/api/core/config.py` | All environment variables |
| `apps/api/core/exceptions.py` | Error types and their HTTP status codes |
| `apps/api/routers/command_center.py` | `/command` and `/command/voice` handlers |
| `apps/api/routers/integrations.py` | Google OAuth connect/callback/status |
| `apps/api/routers/replies.py` | Draft CRUD, edit loop, prepare-send, send |
| `apps/api/routers/calendar.py` | Extract, availability, preview, confirm |
| `apps/api/routers/inbox.py` | Email listing, search, sync |
| `apps/api/schemas/agent_response_schema.py` | `AgentResponse` envelope |
| `apps/api/websocket/` | WebSocket connection manager and events |
| `apps/web/app/(app)/command/page.tsx` | Web app's command center for UI reference |