# FRONTEND_STEPS.md
# AI Email Assistant — Frontend Implementation Roadmap

**Audience:** Frontend engineers implementing `apps/web/` end-to-end.
**Companion documents:** `PRD.md`, `TECH_STACK.md`, `STRUCTURE.md`, `BACKEND_STEPS.md`
**Scope:** Everything under `apps/web/` — the Next.js application, including the Command Center (the single voice+text input surface), Dashboard, Inbox, Knowledge Base, Playbooks, Payments (stub), and Settings.

This roadmap is sequential, same convention as `BACKEND_STEPS.md`: nothing in a later phase is built against something that doesn't exist yet. The backend is assumed to already expose the endpoints and WebSocket contract described in `BACKEND_STEPS.md` Phase 20 — if it doesn't yet, build against a mocked API layer (Phase 2.4 sets this up) and swap it out once the real backend is ready, rather than blocking frontend work on backend completion.

> **Auth model note (read before Phase 7):** Per `BACKEND_STEPS.md`, **Clerk owns identity/login/session** — the frontend uses Clerk's Next.js SDK directly for sign-in UI, session state, and token attachment; there is no backend-issued login JWT and no custom `/auth/login` → Google-consent-screen redirect for logging in. **Google OAuth is a separate, post-login *integration* connection** (Gmail/Calendar/Meet access), surfaced as a "Connect Google" action inside the app (Settings, or a first-run prompt) that hits the backend's `routers/integrations.py` (`BACKEND_STEPS.md` Phase 6.0) — not the login screen. Do not build a "Sign in with Google" button that the user mistakes for both at once; if you offer Google as a Clerk *social login* method, that's fine and is still Clerk-owned identity — it does not by itself grant Gmail/Calendar API scopes, which still requires the separate connect flow.

---

## Table of Contents

0. Guiding Rules Before You Start
1. Phase 0 — Toolchain, Accounts & Design Brief
2. Phase 1 — Repository & Folder Skeleton
3. Phase 2 — App Shell Bootstrap (Next.js config, providers, mock API layer)
4. Phase 3 — Design System Foundation (tokens, Tailwind, typography, shadcn/ui)
5. Phase 4 — Core UI Primitives (`components/ui/`)
6. Phase 5 — State Management (Zustand stores, TanStack Query)
7. Phase 6 — API & WebSocket Client Layer
8. Phase 7 — Authentication Flow (Clerk) & Google Account Connection
9. Phase 8 — Global Layout & Persistent Command Center Mount
10. Phase 9 — Command Center: Text Input Path
11. Phase 10 — Command Center: Voice Input Path
12. Phase 11 — Command Center: Assistant Avatar & Conversational Feedback
13. Phase 12 — Approval Gate UI (`ApprovalCard`)
14. Phase 13 — Agent Result Renderers (per-agent cards)
15. Phase 14 — Dashboard Page
16. Phase 15 — Inbox Pages
17. Phase 16 — Knowledge Base Page
18. Phase 17 — Playbooks Page
19. Phase 18 — Settings Pages (incl. VIP Contacts, Google Integration)
20. Phase 19 — Payments Pages (feature-flagged stub)
21. Phase 20 — Real-Time Updates Across the App
22. Phase 21 — Accessibility Pass
23. Phase 22 — Responsive & Mobile Pass
24. Phase 23 — Error Handling, Empty States & Loading States
25. Phase 24 — Frontend Observability (Sentry, analytics)
26. Phase 25 — Testing Strategy
27. Phase 26 — Performance Optimization
28. Phase 27 — CI/CD Pipeline
29. Phase 28 — Deployment (Vercel)
30. Phase 29 — Production Readiness Checklist
31. Appendix A — Environment Variables Reference
32. Appendix B — Build Order Cheat Sheet

---

## 0. Guiding Rules Before You Start

These carry over from the PRD and must hold in every phase below:

1. **The Command Center is the product, not a widget.** It's mounted globally in the root layout (Phase 8) and persists across every route — it is never a page you navigate to, it's a surface that's always there.
2. **Text and voice are two input modes into the exact same pipeline.** One `useCommandCenter` hook, one conversation thread, one backend contract (`AgentResponse`). Voice adds a mic button, a waveform, and spoken output — it does not fork the UI into a separate experience.
3. **Nothing sends/schedules/pays without a visible confirmation step.** Every UI action that maps to a `requires_approval: true` backend response must render `ApprovalCard` and block on an explicit user tap/click — never auto-confirm, never a hidden default-yes.
4. **Raw structured data is never shown to the user as raw structured data.** Whether via the Human Voice Layer (voice) or a properly designed result card (text/visual), results are always rendered in a human-readable form — no dumping JSON in the UI as a placeholder "for now."
5. **Design should feel like a considered product, not a template.** Before writing component code in Phase 3, produce a real design plan (palette, type pairing, layout concept, one signature element) and check it against the "generic AI-generated default" traps — see Phase 3 for specifics.
6. **Accessibility and responsiveness are not a final pass bolted onto a finished app.** Keyboard focus, reduced-motion, and mobile breakpoints are checked at the end of every phase from Phase 4 onward, not deferred entirely to Phase 21–22 (those phases are the audit, not the first attempt).
7. **Identity and integration are two different UI concerns.** "Am I logged in" is answered entirely by Clerk's session state (`useAuth`/`useUser` from Clerk's SDK). "Is my Gmail/Calendar connected" is a separate, independently-failable state read from the backend's `/integrations/google/status` endpoint. A component should never infer login status from Google-connection status or vice versa — see Phase 7.

---

## Phase 0 — Toolchain, Accounts & Design Brief

### 0.1 Install tooling
- Node.js 20+, `pnpm` (preferred for a Turborepo/workspace setup) or `npm`
- VS Code (or equivalent) with Tailwind CSS IntelliSense, ESLint, Prettier extensions

### 0.2 Provision accounts needed by the frontend specifically
- **Vercel project** (deployment target, Phase 28)
- **Clerk application** — the same Clerk application configured in `BACKEND_STEPS.md` Phase 0.2/5. Grab the publishable key for the frontend SDK (`@clerk/nextjs`); the secret key stays server-side only (used by Clerk's Next.js middleware, not exposed to the browser). Clerk — not Auth.js, not a custom flow — owns session truth; this was an open question in earlier drafts and is now settled by the backend roadmap.
- **Sentry project** (frontend DSN, separate from the backend one — Phase 24)
- Confirm the backend's local dev URL and WebSocket URL (from `BACKEND_STEPS.md` Phase 24) so `.env.local` can point at it from day one

### 0.3 Establish the design brief before writing any component
Per the design-system principle (see rule 5 above), do this **before** Phase 3:
- Name the product's single job on first load: for "Priya" (founder persona) opening the app, what's the one thing she should understand in the first second? (Answer drives the Dashboard/Command Center hero treatment in Phase 14.)
- Draft a compact token plan: 4–6 named colors (not generic SaaS-blue-on-white), a display/body typeface pairing appropriate to "a trustworthy executive assistant" tone (not playful, not sterile-enterprise), and one signature element — e.g., the Assistant Avatar's speaking-state animation, or a distinctive way `ApprovalCard` presents a financial/consequential action to signal "this one matters more."
- Explicitly avoid the generic-AI-tool defaults: warm-cream + terracotta, near-black + acid accent, or broadsheet hairline-rule layouts — unless one is a deliberate, justified choice for this specific product, not a default reach.
- Write this plan down in `docs/DESIGN_SYSTEM.md` (create this file now) — Phase 3 implements exactly what's written here, not a fresh improvisation.

**Exit criteria:** `docs/DESIGN_SYSTEM.md` exists with a named palette (hex values), a type pairing, a layout concept for the Command Center + Dashboard, and one named signature element.

---

## Phase 1 — Repository & Folder Skeleton

Scaffold Next.js 15 (App Router) inside `apps/web/`:

```bash
cd ai-email-assistant/apps
npx create-next-app@latest web --typescript --tailwind --app --src-dir=false --import-alias "@/*"
cd web
```

Build out the rest of the folder tree from `STRUCTURE.md` as empty directories/placeholder files. Note the auth route group is no longer `(auth)/login` + `(auth)/callback` (that pair belonged to the old backend-driven OAuth redirect) — Clerk's own hosted/embedded components replace the callback page entirely, and Google connection gets its own route under settings:

```bash
mkdir -p app/{\(auth\)/sign-in,\(auth\)/sign-up,dashboard,inbox/\[emailId\],knowledge-base,playbooks,payments/\[paymentId\],payments/vendors,settings/vip-contacts,settings/payment-policy,settings/integrations}
mkdir -p components/{command-center,voice,email,agents,payments,dashboard,ui}
mkdir -p hooks stores lib styles docs
```

Install core dependencies now (rather than incrementally, so lockfile churn doesn't complicate later phases):

```bash
npm install @clerk/nextjs zustand @tanstack/react-query framer-motion react-hook-form zod \
  lucide-react recharts date-fns
npm install -D @types/node
npx shadcn@latest init
```

**Exit criteria:** `npm run dev` boots the default Next.js starter page at the folder structure matching `STRUCTURE.md`; `npx shadcn@latest init` has produced `components.json` and a working `components/ui/` base.

---

## Phase 2 — App Shell Bootstrap

### 2.1 `next.config.js`
Configure image domains (Gmail avatar/attachment previews), and — critically — set up API rewrites/proxying for local dev so the frontend can call the FastAPI backend without CORS friction (`/api/*` → `http://localhost:8000/*`).

### 2.2 Environment config
Create `.env.local.example` with `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL`, `NEXT_PUBLIC_SENTRY_DSN`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, and `CLERK_SECRET_KEY` (server-only — used by Clerk's Next.js middleware in Phase 7.3, never referenced from client components despite living in the same env file; Next.js only exposes `NEXT_PUBLIC_*`-prefixed vars to the browser, so this is safe as long as it's never accidentally renamed). Never put backend-only secrets (OpenAI keys, Google OAuth client secret, etc.) here — those belong to the backend's `.env`, not the frontend's; the frontend never talks to Google directly, only through the backend's integration router.

### 2.3 Root providers
Create `app/providers.tsx` wrapping the app in: TanStack Query's `QueryClientProvider` and a theme provider (if supporting dark mode per the Phase 0.3 design plan). Clerk's `<ClerkProvider>` wraps the app one level up, in `app/layout.tsx` directly (Phase 8.1) rather than inside this file, since Clerk's Next.js integration expects to be the outermost provider and also drives the middleware-level route protection in Phase 7.3. Mount `providers.tsx` once in `app/layout.tsx` — every later phase assumes these providers (plus Clerk's) are already available via hooks, not re-derived per-page.

### 2.4 Mock API layer (unblocks frontend work if backend isn't ready yet)
Under `lib/`, create `mock-api-client.ts` implementing the same interface as the real `api-client.ts` (built in Phase 6) but returning realistic fixture data for every endpoint (`/command`, `/dashboard`, `/inbox`, `/integrations/google/status`, etc.), matching the `AgentResponse` schema exactly from `BACKEND_STEPS.md` Phase 9.1. Gate which client is used behind `NEXT_PUBLIC_USE_MOCK_API`. This lets Phases 9–19 proceed against realistic data even if the backend's later phases aren't finished yet — swap the flag once real endpoints exist. (Clerk itself is never mocked — even in mock-API mode, use a real Clerk dev instance for sign-in, since Clerk's SDK/session handling isn't something worth faking.)

**Exit criteria:** app boots with providers active; toggling `NEXT_PUBLIC_USE_MOCK_API` between true/false swaps data sources without any component code changes; this toggle has no effect on Clerk sign-in, which always hits the real Clerk dev instance.

---

## Phase 3 — Design System Foundation

Implement exactly what `docs/DESIGN_SYSTEM.md` (Phase 0.3) specified — this phase is execution, not (re-)design.

### 3.1 `tailwind.config.ts`
Extend the default theme with the named palette as CSS custom properties (not hardcoded hex sprinkled through components) — define `--color-*` tokens in `styles/globals.css` and reference them in the Tailwind config's `theme.extend.colors`, so every component pulls from the same source of truth and a future re-theme touches one file.

### 3.2 Typography
Load the chosen display + body typefaces (via `next/font` for self-hosted performance), define a type scale (`text-display-1`, `text-display-2`, `text-body`, `text-caption`, etc.) as Tailwind utilities or a small `Typography.tsx` set of components — not raw `<h1 className="text-4xl font-bold">` scattered ad hoc through every page.

### 3.3 `styles/globals.css`
Base resets, CSS custom properties for the token system, focus-visible styles (accessibility — don't defer this to Phase 21), and reduced-motion media query defaults (`@media (prefers-reduced-motion: reduce)` disabling non-essential animation globally as a baseline, overridden intentionally where motion is essential, e.g., the speaking-avatar pulse).

### 3.4 Signature element spec
Document the one signature element named in Phase 0.3 (e.g., the Avatar's speaking animation, or the `ApprovalCard`'s treatment for high-stakes actions) as a small spec — states, timing, exact motion curve — so it's built once, correctly, in Phase 11/12, not improvised differently each place it appears.

### 3.5 Clerk component theming
Clerk's prebuilt components (`<SignIn />`, `<SignUp />`, `<UserButton />`, used in Phase 7) ship with their own default look. Configure Clerk's `appearance` prop (globally, via `<ClerkProvider appearance={{...}}>` in Phase 8.1) to pull from the same Phase 3.1 tokens, so the sign-in screen doesn't visually read as a bolted-on third-party widget — this is a real instance of rule 5 (no generic-template look), not an exception to it just because Clerk supplies the markup.

**Exit criteria:** a throwaway test page renders the full type scale, color palette swatches, and the signature element's states side by side for design review before any real page consumes them; a quick check of Clerk's `<SignIn />` rendered with the configured `appearance` prop confirms it matches the token palette rather than Clerk's default blue.

---

## Phase 4 — Core UI Primitives (`components/ui/`)

Build/configure the shadcn/ui primitives the rest of the app depends on: `Button`, `Input`, `Textarea`, `Dialog`, `Sheet` (mobile drawer), `Badge`, `Card`, `Skeleton` (loading states), `Toast`, `Tabs`, `Avatar`, `DropdownMenu`, `Tooltip`, `Switch`, `Select`. Re-skin each via the Phase 3 tokens (shadcn's default look must not survive untouched into a "distinctive" product per the design brief) — this is the point where the design plan's typography/color choices actually reach every button and input in the app, not just hero sections.

Every primitive gets a Storybook-style isolated preview (or a `/dev/components` throwaway route if Storybook isn't set up) so component-level accessibility (focus ring visible, correct ARIA roles) is checked here, once, rather than re-verified on every page that happens to use a `Button`.

**Exit criteria:** every primitive renders correctly in light/dark (if applicable) and passes a manual keyboard-only navigation check (tab through, all interactive elements reachable and visibly focused).

---

## Phase 5 — State Management

### 5.1 Zustand stores (`stores/`)
- `commandCenterStore.ts` — conversation thread state, current input mode (text/voice), current agent-in-progress, pending approval state
- `inboxStore.ts` — currently viewed email list, sort/filter state, selected email
- `integrationStore.ts` — Google connection status (`connected`/`disconnected`/`needs_reauth`), granted scopes, last-synced-at — mirrors the backend's `/integrations/google/status` response so components can read connection state without a prop-drilled fetch each time. This is deliberately **not** part of Clerk's own state — Clerk's `useUser()`/`useAuth()` remain the sole source for login identity; this store only ever answers "is Google connected," never "is the user logged in."
- `authStore.ts` — thin convenience store, if needed at all, for non-React-context consumers (e.g., a plain utility function outside a component tree that needs the current Clerk user id). Prefer Clerk's own hooks (`useUser`, `useAuth`) directly inside components rather than mirroring Clerk state into Zustand — Clerk already manages this reactively; duplicating it invites drift. Keep this store minimal (or skip it) unless a concrete non-component use case shows up.
- `paymentsStore.ts` — scaffolded now, unused until Phase 19 (feature-flagged)

Keep stores thin — server data (email lists, dashboard stats) belongs in TanStack Query's cache, not duplicated into Zustand; Zustand is for **client-only UI state** (what's selected, what's open, what mode we're in). Getting this boundary right now avoids a rewrite later when the WebSocket layer (Phase 20) needs to invalidate/update server data correctly.

### 5.2 TanStack Query setup
Define query keys centrally (`lib/query-keys.ts`) so invalidation from the WebSocket layer (Phase 20) can target exact keys without string-matching guesses scattered through components. Include a `integrationStatus` query key (backed by `/integrations/google/status`) alongside the existing dashboard/inbox/etc. keys — this is a real server-state query via TanStack Query, with `integrationStore` (5.1) only holding the derived UI-facing slice if you need optimistic updates around connect/disconnect actions.

**Exit criteria:** a store can be read/written from a throwaway test component and correctly persists across a client-side route navigation (proving it's not accidentally re-initialized per-page).

---

## Phase 6 — API & WebSocket Client Layer

### 6.1 `lib/api-client.ts`
Typed wrapper around `fetch`, one method per backend endpoint from `BACKEND_STEPS.md` Phase 20 (`postCommand`, `postCommandVoice`, `getDashboard`, `searchInbox`, `getEmail`, `createDraft`, `editDraft`, `approveSend`, `previewMeeting`, `confirmMeeting`, `uploadKnowledgeDoc`, `askKnowledge`, `triggerResearch`, `getPlaybooks`, `getVipContacts`, `getSettings`, `getPayments` [stub], `getGoogleIntegrationStatus`, `disconnectGoogleIntegration`). Every method returns a typed response matching `packages/types/` shared types (mirrored from the backend's Pydantic schemas — keep these in sync manually or via a codegen step if the team adopts OpenAPI codegen later).

Attach the auth header using Clerk's session token, not a custom JWT: call Clerk's `getToken()` (from `useAuth()` in a component, or `auth().getToken()` server-side) immediately before each request and set `Authorization: Bearer <clerk_token>`. Do **not** implement a custom silent-refresh-on-401 routine — Clerk's SDK already keeps the session token fresh client-side; a 401 from the backend at this point means the Clerk session itself is genuinely invalid (signed out elsewhere, expired past Clerk's own refresh window), so the correct handling is redirecting to sign-in, not a manual refresh-and-retry loop. Handle a distinct `IntegrationAuthRequiredError`-shaped response (per `BACKEND_STEPS.md` Phase 2.3/6.0.3) by surfacing the Phase 7.4 reconnect prompt instead — this is a different failure from a 401 and must not trigger a logout.

### 6.2 `lib/websocket-client.ts`
Wraps the browser `WebSocket` API: connects to `NEXT_PUBLIC_WS_URL` with a Clerk session token attached (query param or subprotocol, matching whatever the backend's `GET /ws` in Phase 18 expects — Clerk tokens are short-lived, so fetch a fresh one via `getToken()` right before opening the connection, and re-fetch on reconnect rather than reusing a possibly-stale token from the first attempt), auto-reconnects with backoff on drop, and exposes a typed event emitter for the event types defined in `BACKEND_STEPS.md` Phase 18.2 (`email.new`, `email.updated`, `dashboard.refresh`, `draft.updated`, `meeting.proposed`, `agent.status`).

### 6.3 `lib/audio-utils.ts`
Helpers for capturing microphone audio (via `MediaRecorder`), encoding/streaming it to the STT endpoint, and playing back streamed TTS audio (via the Web Audio API) — used by Phase 10.

### 6.4 What must NOT run in the browser
Anything that would expose a provider secret — there shouldn't be any needed client-side, since the backend owns all third-party credentials (OpenAI, Google OAuth client secret, ElevenLabs, etc.) and the frontend only ever holds Clerk's *publishable* key, by design safe for the browser — or that needs server-only Node APIs gets a Next.js Route Handler (`app/api/.../route.ts`) as a thin proxy, rather than being called directly from client components.

**Exit criteria:** `api-client.ts` methods succeed against either the real backend or the Phase 2.4 mock, using a real Clerk session token in both cases; the WebSocket client reconnects correctly when the connection is killed mid-session (test by restarting the backend locally and confirming the frontend recovers without a manual page refresh); a call made with a deliberately expired Clerk token correctly redirects to sign-in rather than looping.

---

## Phase 7 — Authentication Flow (Clerk) & Google Account Connection

This phase now covers two distinct flows that used to be conflated: **signing in** (Clerk, entirely) and **connecting Google** (backend-mediated OAuth, entirely separate, only reachable once already signed in).

### 7.1 `app/(auth)/sign-in/[[...sign-in]]/page.tsx` and `app/(auth)/sign-up/[[...sign-up]]/page.tsx`
Mount Clerk's prebuilt `<SignIn />` / `<SignUp />` components (themed per Phase 3.5). No custom form, no custom redirect-to-backend logic — Clerk handles credential entry, social login (if enabled), magic links, MFA, etc. entirely within these components. There is no `(auth)/callback` page to build: Clerk's components manage their own internal redirect handling and land the user back in the app via Clerk's configured after-sign-in URL (point this at `/dashboard`).

### 7.2 `middleware.ts`
Use `clerkMiddleware()` (from `@clerk/nextjs/server`) at the app root to protect routes: define which route groups require a signed-in session (everything except `(auth)/*`) and redirect unauthenticated requests to `/sign-in`. This replaces the old custom JWT-checking middleware entirely — there is no backend token to validate here, only Clerk's own session cookie, which the middleware helper handles natively.

### 7.3 `hooks/useAuth.ts` (thin wrapper, not a reimplementation)
Rather than building custom login/logout/session logic, this hook composes Clerk's own `useUser()` and `useAuth()` (specifically `getToken`, `signOut`) into the shape the rest of the app expects: `user`, `isAuthenticated`, `logout()`, `getAuthToken()`. Keep it thin — its job is giving the rest of the codebase one stable import rather than reaching into `@clerk/nextjs` everywhere, not adding behavior Clerk doesn't already provide. There is no `login()` here needing custom OAuth-redirect logic — that's just Clerk's `<SignIn />` from 7.1, or `openSignIn()` if triggering it from a non-route context (e.g., a modal).

### 7.4 Google account connection UI (`components/settings/GoogleIntegrationCard.tsx`)
This is the flow that used to live at `/login`; it now lives in Settings (Phase 18) and is also surfaced as a **first-run prompt** right after sign-up, since the product can't do anything Gmail-related until it's connected:
- Shows current status (`connected` / `not connected` / `needs reattention`, from `integrationStore`/the `/integrations/google/status` query) and granted scopes in plain language.
- "Connect Google" button → navigates to the backend's `/integrations/google/connect` (a full-page redirect, not a fetch call, since it needs to hit Google's actual consent screen) — this endpoint requires the Clerk session to already be valid, which it will be, since this screen is behind the Phase 7.2 middleware.
- On return from Google's consent flow (backend's `/integrations/google/callback` redirects back into the app, e.g. to `/settings/integrations?connected=true`), refetch integration status and show a success state.
- "Disconnect" button → calls `disconnectGoogleIntegration()` and updates state — must not touch the Clerk session at all; a disconnected-Google user is still fully signed in and can still browse non-Gmail parts of the app (Playbooks, Settings, Knowledge Base not yet populated, etc.).

### 7.5 Incremental scope re-request UI
Per PRD 10/13.1, when the user's first scheduling or send action needs a scope they haven't granted yet, the backend signals this via `IntegrationAuthRequiredError` (not a 401 — see Phase 6.1). Build a small `ScopeUpgradePrompt` component (in `components/command-center/` or `components/ui/`) that explains in plain language what's being requested and why ("To schedule this meeting, I need access to your Calendar") before sending the user through the same `/integrations/google/connect` redirect from 7.4, scoped to just the missing permission. Never silently fail a command because of a missing scope without this explanation, and never confuse this with a sign-in prompt — the user is already authenticated; only reuse the Clerk sign-in UI if `getToken()` itself starts failing, which is a genuinely different problem.

**Exit criteria:** sign-up → sign-in → `/dashboard` flow works end-to-end against a real Clerk dev instance with zero custom OAuth code; signing out via `useAuth().logout()` clears all client state (Zustand stores reset, Query cache cleared) and redirects to `/sign-in`; an expired Clerk session correctly redirects to sign-in rather than showing a broken authenticated page; **separately**, a signed-in user with no Google connection can browse the app, sees a clear "connect Google" prompt where relevant, completes the connect flow, and lands back with `google_integrations` populated (verified against the backend); disconnecting Google leaves the user signed in and able to use non-Gmail features; a simulated `IntegrationAuthRequiredError` on a calendar command triggers `ScopeUpgradePrompt`, not a logout.

---

## Phase 8 — Global Layout & Persistent Command Center Mount

### 8.1 `app/layout.tsx`
This is the file that makes the Command Center global rather than a per-page feature (matches PRD 5.1's "front door" framing), and is also where Clerk's provider wraps everything. Structure:
```
<html>
  <body>
    <ClerkProvider appearance={...}>   (Phase 3.5 tokens)
      <Providers>                       (Phase 2.3 — Query, theme)
        <AppShell>                       — persistent nav/sidebar
          {children}                     — the current route's page content
          <CommandCenter />               — floats/docks globally, on every route
        </AppShell>
      </Providers>
    </ClerkProvider>
  </body>
</html>
```

### 8.2 `AppShell` navigation
Build the persistent nav (sidebar or top bar, per the Phase 0.3 layout concept) linking to Dashboard, Inbox, Knowledge Base, Playbooks, Payments, Settings — this is standard app chrome, but must not visually compete with the Command Center for primacy, since the PRD's product thesis is "the AI Command Center is her inbox," not a traditional nav-first app. Include Clerk's `<UserButton />` (themed per 3.5) in the nav for account/session management (profile, sign-out) — don't build a custom account dropdown that duplicates what Clerk already provides.

### 8.3 Route groups
Confirm the `(auth)` route group (now `sign-in`/`sign-up`, per Phase 7.1) correctly excludes the `AppShell`/`CommandCenter` chrome (a logged-out user on `/sign-in` shouldn't see a floating assistant for an account they haven't accessed yet). Also confirm `/settings/integrations` **is** inside the authenticated chrome (it needs `AppShell`/nav like any other settings page) — it's a post-login settings page, not part of the `(auth)` group, even though it deals with OAuth.

**Exit criteria:** navigating between `/dashboard`, `/inbox`, `/knowledge-base` etc. keeps the Command Center mounted and its conversation state intact (proving it's a layout-level mount, not remounted per page — verify by starting a command on one page and confirming its result still renders after navigating away and back); `<UserButton />` sign-out correctly triggers the full Phase 7 logout behavior.

---

## Phase 9 — Command Center: Text Input Path

Build the simpler path first — this exercises the whole pipeline (input → Supervisor → agent → result) without voice's added complexity, and everything from Phase 11 onward reuses it.

### 9.1 `components/command-center/CommandBar.tsx`
The single input box. A text `<Input>` (or `<Textarea>` for longer dictated/typed replies) with a submit action (Enter key + a send button), plus the mic icon reserved for Phase 10. On submit: call `useCommandCenter`'s `sendTextCommand(text)`.

### 9.2 `components/command-center/useCommandCenter.ts`
The core hook. On `sendTextCommand`:
1. Append the user's message to `commandCenterStore`'s conversation thread immediately (optimistic UI — don't wait for the round trip to show what the user typed).
2. Call `api-client.postCommand(text, sessionContext)` (which internally attaches the Clerk token per Phase 6.1).
3. On response, branch on `AgentResponse.status`:
   - `completed` → render result via the appropriate agent card (Phase 13)
   - `clarification_needed` → render the clarifying question as an assistant message, keep input focused for the reply
   - `waiting_for_user` → render the in-progress state (e.g., a draft that's mid-edit-loop) and keep the relevant agent "session" active client-side
   - `error` → render a clear, in-voice-of-the-interface error message (per the design brief's writing guidance — explain what happened, not a stack trace)
4. If `requires_approval: true`, render `ApprovalCard` (Phase 12) instead of/alongside the raw result — never auto-render a "confirmed" state.
5. If the call fails with the Phase 6.1 `IntegrationAuthRequiredError` shape (e.g., the command needed Gmail access and it's not connected/has been revoked), render the Phase 7.5 `ScopeUpgradePrompt` inline in the thread rather than a generic error bubble — this is a recoverable, expected state, not a failure.

### 9.3 `components/command-center/ConversationThread.tsx`
Renders the full back-and-forth: user messages (text or "🎤 [transcript]" for voice, built in Phase 10), assistant responses (text, or one of the Phase 13 agent cards, an `ApprovalCard`, or a `ScopeUpgradePrompt`), in chronological order, auto-scrolling to the latest turn.

### 9.4 Multi-turn context (edit loops)
For Reply/Calendar agent sessions that stay alive across turns (per `BACKEND_STEPS.md` Phase 12.4/13.3), `useCommandCenter` must route a follow-up command like "shorten it" to the same in-progress draft/preview session rather than starting a new intent classification from scratch — track the "active session" (draft ID / meeting preview ID) in `commandCenterStore` and pass it along on every subsequent command until that flow completes or is cancelled.

**Exit criteria:** typing "show me my unread emails" produces a rendered inbox-summary card in the thread; typing "reply to it" with no prior context produces a clarification message; a full "draft → shorten it → send it → approve" text-only flow completes end-to-end against the mock (or real) API with the approval step correctly blocking until confirmed; a command requiring an unconnected Google scope produces the `ScopeUpgradePrompt` inline rather than a generic error.

---

## Phase 10 — Command Center: Voice Input Path

Layered on top of Phase 9 — voice never forks into a separate pipeline, it feeds the same `useCommandCenter`.

### 10.1 `hooks/useMicRecorder.ts`
Wraps `MediaRecorder` (via `lib/audio-utils.ts`): `startRecording()`, `stopRecording()`, streams audio chunks to the backend's `/command/voice` endpoint (or buffers and sends on stop, depending on what the backend's STT integration supports — streaming preferred per PRD 5.4). Handle mic permission denial gracefully with a clear inline message, not a silent failure.

### 10.2 `components/voice/VoiceVisualizer.tsx`
Live waveform/pulse driven by the mic's audio level while recording, giving real-time feedback that the system is listening — this is part of "feels like talking to someone," not a decorative extra.

### 10.3 Live transcript preview
Per PRD 5.4's edge case for long dictated replies: as partial transcripts stream back from STT, show them live in the `CommandBar` (replacing/supplementing the placeholder) so the user can interrupt or correct before the full command is submitted — do not wait silently until recording stops to show anything.

### 10.4 Wiring into `useCommandCenter`
Add `sendVoiceCommand(audioStream)` alongside `sendTextCommand`, converging on the exact same response-handling branch (9.2 step 3–5) once a transcript comes back — this is the guarantee that voice and text are one pipeline, not two.

### 10.5 `hooks/useTextToSpeechPlayer.ts`
Plays back the audio returned from the backend's Human Voice Layer (`BACKEND_STEPS.md` Phase 8.5) for voice-mode responses only — text-mode responses never trigger this. Handle playback interruption (user starts a new command while a response is still being spoken — stop playback immediately, don't queue).

### 10.6 Low-confidence transcription handling
Per PRD 5.4, if the backend signals low STT confidence on a consequential command (reply/send/schedule/pay), the UI must show "I didn't quite catch that — can you repeat it?" rather than proceeding — implement this as a distinct `AgentResponse.status` branch, not a generic error.

**Exit criteria:** tapping the mic, speaking a command, and seeing/hearing the same result quality as the equivalent typed command (same `ConversationThread` rendering, same `ApprovalCard` behavior); interrupting a spoken response by issuing a new command stops audio playback immediately; a simulated low-confidence transcript triggers the repeat-prompt instead of executing.

---

## Phase 11 — Command Center: Assistant Avatar & Conversational Feedback

### 11.1 `components/command-center/AssistantAvatar.tsx`
Implements the Phase 3.4 signature element spec. States: `idle → listening → thinking → speaking`, each with a distinct, deliberate visual treatment (per the design brief — this is very likely the product's one "spend your boldness here" moment). Synced to: mic recording state (listening), pending API call (thinking), TTS audio playback (speaking, mouth/pulse animated in time with audio via the Web Audio API's amplitude data, not a generic looping animation).

### 11.2 Tone-aware rendering
The backend's Human Voice Layer (`BACKEND_STEPS.md` Phase 8.5.3) selects a tone (casual/careful/calm) per response — reflect this subtly in the UI too, not just the audio: e.g., `ApprovalCard` and fraud-flagged results get a visually distinct, more serious treatment than a casual daily-triage summary, so the tone is legible even to a user who has sound off.

### 11.3 Respect reduced motion
The Avatar's animations must degrade to a static or minimally-animated state under `prefers-reduced-motion`, per Phase 3.3's global baseline — this is a real accessibility requirement, not optional polish.

**Exit criteria:** all four avatar states are visually distinct and correctly triggered by real app state (not manually toggled for a demo); reduced-motion mode confirmed via OS-level setting to suppress the speaking-pulse animation while still indicating state through a non-motion cue (e.g., a color or icon change).

---

## Phase 12 — Approval Gate UI

### 12.1 `components/command-center/ApprovalCard.tsx`
Generic, reused for send / schedule / pay — per PRD 9.10's `requires_approval` flag, this component is the UI's single enforcement surface: it must be the only path by which a consequential `AgentResponse` can be confirmed. Props: `actionType` ('send' | 'schedule' | 'pay'), `preview` (recipient/subject/body, or time/attendees/Meet link, or invoice/vendor/amount), `onApprove`, `onReject`. Renders full, unambiguous preview content — never a vague "are you sure?" without showing exactly what will happen.

### 12.2 Explicit confirmation interaction
Require a real tap/click on an "Approve"/"Send"/"Confirm" button — never a voice command alone silently confirms without this card having been shown and acted on (matches PRD 5.7's "there is no voice shortcut that bypasses approval"). If voice mode, the card is still rendered, and TTS asks the confirmation question (Phase 8.5.4 on the backend), but the actual state transition happens through the UI action, giving a natural point for the user to review before committing.

### 12.3 Fraud/policy warnings (forward-compat for Payment Agent)
Build `FraudWarningBanner.tsx` and `PolicyCheckBadge.tsx` (under `components/payments/`) now, even though Payment Agent is backend-disabled — `ApprovalCard` should already support an optional warning-banner slot so wiring in real payment approvals later (post-MVP) doesn't require touching this shared component again.

**Exit criteria:** a send/schedule/pay flow cannot reach a "confirmed" state without this component having rendered and its approve action having fired; a rejected/cancelled approval correctly returns the agent session to a safe, resumable state (e.g., draft still editable) rather than discarding work.

---

## Phase 13 — Agent Result Renderers

One card component per agent, each consuming its slice of `AgentResponse.result`:

- `ReplyDraftCard.tsx` — draft body (editable inline), edit-command affordances ("shorten," "make warmer" as quick-action chips, plus free-text edit), send button (routes through `ApprovalCard`)
- `MeetingPreviewCard.tsx` — proposed time(s) with timezone labels, attendee list (editable per PRD 5.8 edge case), Meet link, confirm button (routes through `ApprovalCard`)
- `ResearchReportCard.tsx` — structured report display (Executive Summary, SWOT, Competitors, Opportunities, Risks) with per-claim source/timestamp citations, collapsible sections for a long report
- `KnowledgeAnswerCard.tsx` — answer text with inline source citations; explicit "not found in Company Memory" state (never render a fabricated-looking answer with no citation)
- `PaymentPreviewCard.tsx` — scaffolded now per Phase 12.3, inert until Payment Agent ships

Every card must handle its own **loading** and **error** sub-states (skeleton while the agent is still working, clear error message on `status: error`) — don't rely on a single global spinner for all agent types, since the interaction shapes differ (a draft-in-progress looks different from a research report still crawling).

**Exit criteria:** each card renders correctly against realistic fixture data (from the Phase 2.4 mock) for both its happy path and its documented PRD edge cases (e.g., `ResearchReportCard` correctly shows "source could not be accessed" per PRD 5.12).

---

## Phase 14 — Dashboard Page

### 14.1 `app/dashboard/page.tsx`
Per PRD 5.3: new email count, high-priority count, unread count, meeting requests detected, pending replies, follow-up reminders, AI-recommended next actions. This is the "one thing understood in the first second" moment named in Phase 0.3 — design it as the actual hero, not a generic stats-grid template. If the signed-in user has no Google connection yet (Phase 7.4 status), this page should lead with a prominent connect-Google prompt instead of empty stat tiles — an empty dashboard for an unconnected account is a setup-incomplete state, not a "zero emails" state, and should look different from both.

### 14.2 `components/dashboard/SummaryStats.tsx`, `PriorityList.tsx`
Stat tiles and a prioritized email list, both driven by TanStack Query against `getDashboard()`, updated live via the Phase 20 WebSocket subscription (no manual refresh needed, per PRD 5.3).

### 14.3 `components/dashboard/PendingPaymentsWidget.tsx`
Scaffolded, hidden behind the payments feature flag until Phase 19/Payment Agent ships.

### 14.4 First-login bounded window
Per PRD 5.3's edge case, show only a recent bounded window (e.g., last 7 days) with a progress indicator for async historical backfill on first login **after Google is connected** — a genuinely new Clerk sign-up with no Google connection yet has nothing to backfill at all, so this indicator only appears once 7.4's connect flow has completed. Don't block the whole dashboard render on a full historical sync.

**Exit criteria:** dashboard renders correctly with zero, some, and a large (100+) volume of emails, and separately with Google not yet connected at all (distinct empty state, per 14.1); a live WebSocket event (simulated) updates a stat tile without a page refresh; first-login backfill progress indicator is visible and updates.

---

## Phase 15 — Inbox Pages

### 15.1 `app/inbox/page.tsx`
Email list view (`components/email/EmailListItem.tsx`), backed by natural-language and structured search/filter, paginated (default 25 per PRD 5.5), with a friendly empty state on zero results (not a blank screen). If Google isn't connected, this route should redirect to or embed the Phase 7.4 connect prompt rather than showing a broken/empty list — same principle as 14.1.

### 15.2 `app/inbox/[emailId]/page.tsx`
Full email viewer (`EmailViewer.tsx`, `ThreadView.tsx`) — AI summary, thread summary, key action items, detected deadlines, suggested next actions ("Reply," "Schedule meeting," "Add to knowledge base") per PRD 5.6. Large attachments show a preview for supported types, metadata + download link otherwise.

### 15.3 List-order/index resolution
Per PRD 5.1's edge case, "open the first email" resolves against the currently rendered list order — ensure the frontend's list state (post sort/filter) is exactly what `commandCenterStore`'s context updates reference, so Command Center references and manual clicks always agree on "which one is first."

**Exit criteria:** searching, opening, and acting on an email (via both direct click and via a Command Center command referencing "the second one") produce consistent results; a 50+ message thread renders its hierarchical summary correctly without layout breakage; visiting `/inbox` with Google disconnected shows the connect prompt, not an error or empty list.

---

## Phase 16 — Knowledge Base Page

### 16.1 `app/knowledge-base/page.tsx`
Document upload (drag-drop + file picker, PDF/DOCX/TXT/MD/CSV per PRD 5.9), list view with per-document `indexing_status` (queued/processing/ready/failed) polled or WebSocket-updated, and a direct-question interface reusing `KnowledgeAnswerCard` (Phase 13). Note this page has no dependency on Google being connected at all — it's fully usable by a signed-in user who hasn't connected Gmail yet, which is worth calling out in the empty/onboarding state rather than gating it behind the same connect prompt as Inbox/Dashboard.

### 16.2 Conflict & access-level display
Surface the "conflicting documents" case (PRD 5.9) clearly when it occurs — two source badges with dates, not a merged/ambiguous answer. Respect document-level access control (PRD 13.4) — a Member-role user should not see Admin-only documents in the list at all, not just be blocked from opening them.

**Exit criteria:** uploading a real PDF/DOCX shows correct status transitions through to "ready," and a direct question against it returns a cited answer; a restricted document is invisible to a lower-privilege test account.

---

## Phase 17 — Playbooks Page

`app/playbooks/page.tsx` — CRUD list/detail for reusable reply templates (PRD 5.10). Simple form-based editor (React Hook Form + Zod validation) for scenario type, template structure, tone settings. No agent interaction needed here beyond standard CRUD against the backend's `routers/playbooks.py`. Like Knowledge Base, this page doesn't require Google to be connected.

**Exit criteria:** create/edit/delete a playbook and confirm it correctly influences a subsequent Reply Agent draft (cross-check against Phase 9/13's `ReplyDraftCard` flow).

---

## Phase 18 — Settings Pages

### 18.1 `app/settings/page.tsx`
General preferences: language, timezone, voice profile selection (feeds `tts_client` on the backend), notification preferences.

### 18.2 `app/settings/integrations/page.tsx`
Hosts the `GoogleIntegrationCard` built in Phase 7.4 — connection status, granted scopes, connect/disconnect actions. This is the durable home for Google account management; the first-run prompt (7.4) is just a contextual nudge that links here. If the product later adds more integrations (Slack, Notion, etc.), this page is where they'd each get their own status card, following the same pattern.

### 18.3 `app/settings/vip-contacts/page.tsx`
CRUD for VIP contacts (PRD 5.11) — simple list + add/remove, explaining plainly what VIP status changes ("always shown as high priority").

### 18.4 `app/settings/payment-policy/page.tsx`
Scaffolded, feature-flagged off (thresholds/approver rules) — matches backend Phase 17's inert Payment Agent.

### 18.5 Account management
For profile editing, email/password changes, and account deletion, prefer Clerk's own `<UserProfile />` component (linked from `<UserButton />` in Phase 8.2, or embedded at `app/settings/account/page.tsx`) over building custom forms — Clerk already handles this UI, themed per Phase 3.5. Only build a custom account page if the design brief specifically calls for something Clerk's component can't do.

**Exit criteria:** settings changes persist and are reflected immediately elsewhere in the app (e.g., changing timezone updates how the Command Center displays relative times without a reload); `/settings/integrations` correctly reflects connect/disconnect actions and matches what `/dashboard`'s and `/inbox`'s connect prompts show, with no state drift between them.

---

## Phase 19 — Payments Pages (Feature-Flagged Stub)

Build `app/payments/page.tsx`, `[paymentId]/page.tsx`, `vendors/page.tsx`, and the `components/payments/*` list items — but gate the entire section behind the same feature flag the backend uses (`NEXT_PUBLIC_PAYMENT_AGENT_ENABLED`, mirroring `BACKEND_STEPS.md`'s `PAYMENT_AGENT_ENABLED`). When disabled, the nav item and routes should either be hidden entirely or show a clear "coming soon" state — never a broken/empty page reachable by direct URL.

**Exit criteria:** with the flag off, `/payments` is not reachable/visible; with the flag on (test environment only), the pages render correctly against mock data and route consequential actions through `ApprovalCard` exactly like every other agent.

---

## Phase 20 — Real-Time Updates Across the App

### 20.1 `hooks/useWebSocket.ts`
Central hook subscribing to the `lib/websocket-client.ts` connection (Phase 6.2), dispatching incoming events to the right place: `dashboard.refresh` → invalidate the Phase 5.2 dashboard query key; `email.new`/`email.updated` → invalidate/patch the inbox list query; `draft.updated` → sync `ReplyDraftCard` if that draft is currently open; `agent.status` → update in-progress indicators in `ConversationThread`. Also invalidate the `integrationStatus` query key (Phase 5.2) whenever the WebSocket connection re-establishes after a drop, since a Google token could have been silently revoked while disconnected.

### 20.2 Multi-tab/device consistency
Per PRD 5.3's edge case, verify that two open tabs for the same user both receive and correctly render the same live update — this is largely a backend guarantee (`BACKEND_STEPS.md` Phase 18.1), but the frontend must not have any tab-local-only state that would cause the two tabs to visibly diverge after the same event. This includes Google-connection state: connecting Google in one tab should reflect as connected in a second open tab (via a WebSocket-triggered invalidation or a simple refetch-on-focus), not require a manual reload of the other tab.

**Exit criteria:** a background email arrival (simulated) updates the Dashboard and Inbox list live, in two simultaneously open tabs, without either needing a manual refresh.

---

## Phase 21 — Accessibility Pass

Audit the whole app against WCAG 2.1 AA (PRD 6):
- Full keyboard-only pass through every flow built in Phases 9–19 (Command Center text flow, approval flows, settings forms, and the Clerk sign-in/sign-up flow from Phase 7 — Clerk's components are generally accessible out of the box, but verify the themed version from Phase 3.5 hasn't broken focus states) — every interactive element reachable and visibly focused, no keyboard traps in `Dialog`/`Sheet` components.
- Screen-reader pass (VoiceOver/NVDA) on the Command Center specifically — confirm the conversation thread announces new messages (`aria-live` region), and that voice-mode state changes (listening/thinking/speaking) are conveyed non-visually too.
- Color contrast check against the Phase 3 token palette for all text/background pairs, including inside `ApprovalCard` and status badges.
- Confirm reduced-motion behavior (Phase 11.3) holds across every animated component, not just the Avatar.

**Exit criteria:** an automated audit (axe-core or equivalent) run against every major page returns no critical/serious violations; a full manual keyboard-only run-through of the "type a command → get a draft → send it" flow succeeds without a mouse.

---

## Phase 22 — Responsive & Mobile Pass

Verify every phase's output down to a small mobile viewport (not just "it doesn't break," but "it's genuinely usable one-handed," per PRD's founder-persona use case of managing email while mobile):
- Command Center's `CommandBar` + Avatar reflow sensibly on mobile (likely docked/collapsible rather than always-expanded).
- `Sheet` (mobile drawer) used for `ApprovalCard` and agent result cards on small viewports instead of the desktop inline card layout, if the design plan calls for it.
- Inbox list/detail follows a standard responsive master-detail pattern (list-only → tap in → detail view with back navigation) rather than a squeezed two-pane desktop layout.
- Voice input (mic button, waveform) is comfortably tappable and visible on mobile — this is arguably the most important mobile case per PRD 5.4's "driving/walking" use case.
- Clerk's `<SignIn />`/`<SignUp />`/`<UserProfile />` components render sensibly at mobile widths (they generally do by default, but confirm against the themed version from 3.5).

**Exit criteria:** every page from Phases 14–19 is manually verified at a small phone viewport width and a tablet width, with no horizontal scroll, no overlapping elements, and all touch targets meeting a reasonable minimum size.

---

## Phase 23 — Error Handling, Empty States & Loading States

Systematic pass across the whole app (don't rely on Phase 9–19 having caught every case inline):
- Every data-fetching page has a defined loading (skeleton, not spinner-only where content shape is known), empty (per the design brief's "an empty screen is an invitation to act" principle — e.g., empty Knowledge Base should prompt an upload, not just say "no documents"), and error state (explained in the interface's voice, with a retry action where sensible).
- Network failure / backend-down scenarios (kill the backend locally, confirm the app degrades to a clear "can't reach the assistant right now" state rather than an infinite spinner or silent failure) — critical given the Command Center is the primary interface. Note Clerk sign-in itself doesn't depend on the FastAPI backend being up at all (it's a direct Clerk SDK call) — confirm a killed backend still allows sign-in to succeed and correctly shows the "can't reach the assistant" state only for backend-dependent screens, not a global broken-app state.
- Google-not-connected and Google-connection-revoked are their own defined states (Phases 7.4, 14.1, 15.1) — distinct from both "loading" and "generic error."
- Form validation errors (Zod + React Hook Form across Playbooks/Settings/VIP Contacts) are inline, specific, and non-blocking of unrelated fields.

**Exit criteria:** every page in the app has been manually tested with the backend killed, with a fresh empty account, with Google not connected, and with a deliberately-triggered validation error, and each produces a clear, on-brand message rather than a generic Next.js error boundary or blank page.

---

## Phase 24 — Frontend Observability

### 24.1 Sentry
Wire `@sentry/nextjs` for both client and server-side error capture, with user/session context attached (Clerk's user id is a natural fit here, without leaking PII beyond what's already visible to the user themselves) and source maps uploaded on build for readable stack traces.

### 24.2 Product analytics (approval-vs-abandon tracking)
Per PRD 17.2's named product health metric, instrument events for: draft shown → sent vs. abandoned, meeting proposed → confirmed vs. abandoned, so the "approval-vs-abandon rate" the PRD calls out as a key signal is actually measurable, not just a backend log line with no frontend funnel context. Also instrument a Google-connect funnel (prompt shown → connect started → connect completed vs. abandoned) since it's now a distinct, potentially-drop-off-prone step separate from sign-up.

### 24.3 Web Vitals
Report Core Web Vitals (LCP, INP, CLS) via Next.js's built-in reporting to your analytics/monitoring backend, tracked especially for the Dashboard and Command Center's first interaction (this is the highest-frequency surface per the PRD's vision).

**Exit criteria:** a deliberately-thrown frontend error appears in Sentry with correct source-mapped stack trace and user context; a full draft-to-send flow correctly emits the funnel events needed to compute approval-vs-abandon rate; a simulated Google-connect flow emits its funnel events correctly.

---

## Phase 25 — Testing Strategy

- **Component tests** (Vitest/Jest + React Testing Library) for every `components/agents/*` card, `ApprovalCard`, `GoogleIntegrationCard`, `ScopeUpgradePrompt`, and Command Center pieces — especially the branching logic in `useCommandCenter` (Phase 9.2's status branches, including the `IntegrationAuthRequiredError` branch) since that's the highest-leverage piece of frontend logic in the app.
- **Integration tests** against the Phase 2.4 mock API layer for full page flows (Dashboard load, Inbox search-and-open, Knowledge Base upload-and-ask, Settings → Integrations connect/disconnect).
- **E2E tests** (Playwright) for the critical paths named across this document: full text-mode "draft → edit → send" flow, full voice-mode equivalent (mocking STT/TTS at the network boundary), meeting scheduling preview-to-confirm, the Clerk sign-up/sign-in round trip (against a real Clerk test/dev instance — Clerk explicitly supports this for E2E), and the separate Google-connect round trip (against a sandboxed Google test account, matching `BACKEND_STEPS.md` Phase 22's integration test setup).
- **Visual regression** (Playwright screenshots or Chromatic) specifically on `AssistantAvatar` states and `ApprovalCard` variants, since these are the components most likely to visually drift without anyone noticing in a code review.
- **Accessibility tests** (axe-core integrated into the E2E suite) run in CI, not just manually in Phase 21 — that phase establishes the baseline, this phase prevents regression.

**Exit criteria:** CI blocks merge on any failing component/integration/E2E/accessibility test; the critical E2E paths — including both the Clerk auth round trip and the Google-connect round trip as separate, independently-passing tests — run against a staging-like environment on every PR to `main`.

---

## Phase 26 — Performance Optimization

- Code-split agent result cards and the Payments section (Phase 19) via dynamic imports so users who never trigger Research or Payments don't pay that bundle cost upfront.
- Verify `next/image` is used for all attachment/avatar previews with correct sizing to avoid layout shift (feeds directly into the Phase 24.3 CLS metric).
- Confirm TanStack Query cache/staleness settings avoid redundant refetches on route navigation (e.g., navigating Dashboard → Inbox → Dashboard shouldn't re-fetch dashboard stats that are still fresh, and shouldn't needlessly re-fetch `integrationStatus` on every route change either).
- Audit the WebSocket event handlers (Phase 20) for unnecessary full-list re-renders on high-frequency events (e.g., a burst of `email.new` events during backfill should batch-update the list, not re-render per event).

**Exit criteria:** Lighthouse/Web Vitals scores meet the PRD's implied performance bar (Command Center response should feel instantaneous for the optimistic-UI text path per Phase 9.2 step 1, even while the network call is in flight); bundle analysis confirms Payments/Research code isn't in the initial JS payload for a fresh Dashboard load.

---

## Phase 27 — CI/CD Pipeline

Mirror the backend's structure (`infra/ci-cd/github-actions/deploy-web.yml`, referenced in `BACKEND_STEPS.md` Phase 25):
- On every PR: lint (`eslint`), type-check (`tsc --noEmit`), unit/component tests, E2E tests (Phase 25, using Clerk's testing tokens / a dedicated Clerk test instance so the auth E2E test doesn't depend on real email delivery) against a preview deployment.
- Vercel's native PR preview deployments serve as the staging step — each PR gets a real, shareable URL for design/product review before merge. Ensure preview deployments are configured with a Clerk dev/test instance key (not production Clerk credentials) via Vercel's per-environment env vars.
- On merge to `main`: production deployment via Vercel, with the same manual-promotion-gate pattern as the backend if the team wants an extra checkpoint before it's live (optional for frontend, since Vercel's preview-then-promote model already provides a safety net).

**Exit criteria:** a PR with a failing type-check or test is blocked from merge; every PR produces a working preview URL automatically, correctly wired to a non-production Clerk instance.

---

## Phase 28 — Deployment (Vercel)

Connect the Vercel project to the repo (scoped to `apps/web/` if using a monorepo), configure environment variables per environment (dev/staging/prod) matching Appendix A below — critically, a **production Clerk instance key**, distinct from the dev/test one used in Phase 27 — and point `NEXT_PUBLIC_API_URL`/`NEXT_PUBLIC_WS_URL` at the corresponding backend environment from `BACKEND_STEPS.md` Phase 26. Confirm custom domain + HTTPS is configured for production, and that Clerk's dashboard has the production domain's redirect URLs allow-listed.

**Exit criteria:** a full onboarding flow (PRD 7.1) — sign-up through Clerk, connecting Google via the separate integration flow, guided setup, first Command Center interaction — completes successfully against the deployed production frontend talking to the deployed staging/production backend.

---

## Phase 29 — Production Readiness Checklist

- [ ] Command Center works identically (same result quality, same approval gating) via both text and voice, verified side-by-side.
- [ ] No consequential action (send/schedule/pay) reachable without `ApprovalCard` having rendered and been explicitly confirmed — verified via the Phase 25 E2E suite, not just code review.
- [ ] Sign-in/sign-up works end-to-end against production Clerk; Google connect/disconnect works end-to-end against the production backend's integration router, independently of Clerk session state in both directions.
- [ ] Every page has defined loading/empty/error states (Phase 23) — no default Next.js error boundary visible anywhere in a manual walkthrough — including the Google-not-connected and Google-revoked states specifically.
- [ ] Full app passes the Phase 21 accessibility audit and Phase 22 mobile pass.
- [ ] Sentry actively receiving frontend errors from staging traffic; approval-vs-abandon and Google-connect funnel events confirmed flowing to analytics.
- [ ] Design system tokens (Phase 3) are the only source of color/type/spacing across the app, including the themed Clerk components — no stray hardcoded values from a `grep` audit of `className` strings for raw hex codes.
- [ ] Payments section correctly hidden/inert with the feature flag off in production.
- [ ] Multi-tab/multi-device live-update consistency (Phase 20.2) verified against the real deployed backend, not just mocked — including Google-connection-status consistency across tabs.
- [ ] Rollback plan confirmed (Vercel instant rollback to a previous deployment).

---

## Appendix A — Environment Variables Reference

| Variable | Introduced In | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Phase 2 | Backend REST base URL |
| `NEXT_PUBLIC_WS_URL` | Phase 2 | Backend WebSocket URL |
| `NEXT_PUBLIC_USE_MOCK_API` | Phase 2.4 | Toggle mock vs. real API client (never affects Clerk) |
| `NEXT_PUBLIC_SENTRY_DSN` | Phase 0.2 / 24 | Frontend error tracking |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Phase 0.2 / 7 | Clerk frontend SDK — identity/session (required, not optional) |
| `CLERK_SECRET_KEY` | Phase 2.2 / 7.2 | Server-only — used by `clerkMiddleware()`; never sent to the browser |
| `NEXT_PUBLIC_PAYMENT_AGENT_ENABLED` | Phase 19 | Feature flag, mirrors backend flag |

Note: there is **no** `NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID` or similar here — the frontend never talks to Google directly. The Google OAuth client id/secret live only in the backend's environment (`BACKEND_STEPS.md` Appendix A); the frontend only ever navigates the browser to the backend's `/integrations/google/connect` URL and lets the backend own the Google-facing side of that redirect.

---

## Appendix B — Build Order Cheat Sheet

```
0.  Toolchain, accounts (incl. Clerk app), design brief written down
1.  Folder skeleton (Next.js App Router + STRUCTURE.md layout; sign-in/sign-up routes, not login/callback)
2.  App shell bootstrap (config, providers, mock API layer — Clerk never mocked)
3.  Design system foundation (tokens, typography, signature element spec, Clerk appearance theming)
4.  Core UI primitives (components/ui/, re-skinned shadcn)
5.  State management (Zustand stores incl. integrationStore + TanStack Query)
6.  API client + WebSocket client (Clerk token attached) + audio utils
7.  Auth (Clerk SignIn/SignUp/middleware/useAuth) + separate Google account connection flow
8.  Global layout + ClerkProvider + persistent Command Center mount
9.  Command Center — text input path (incl. IntegrationAuthRequiredError branch)
10. Command Center — voice input path (layered on #9)
11. Assistant Avatar + tone-aware conversational feedback
12. Approval Gate UI (ApprovalCard — the enforcement surface)
13. Agent result renderer cards (one per agent)
14. Dashboard page (incl. Google-not-connected hero state)
15. Inbox pages (list + detail; gated on Google connection)
16. Knowledge Base page (not gated on Google connection)
17. Playbooks page (not gated on Google connection)
18. Settings pages (incl. VIP Contacts, Google Integration card, Clerk UserProfile)
19. Payments pages (feature-flagged stub)
20. Real-time updates wired across every page (incl. integration status)
21. Accessibility pass
22. Responsive/mobile pass
23. Error/empty/loading states systematic pass (incl. Google-disconnected states)
24. Frontend observability (Sentry, funnel analytics incl. Google-connect funnel, Web Vitals)
25. Testing (component, integration, E2E incl. Clerk + Google round trips separately, visual regression, a11y)
26. Performance optimization
27. CI/CD pipeline (Clerk test/dev instance in previews)
28. Vercel deployment (production Clerk instance)
29. Production readiness checklist
```

The Command Center (Phases 9–12) is deliberately built before any "regular" page (Phases 14–19), since every one of those pages either triggers or displays results from it — building it last would mean retrofitting the connection everywhere instead of having it available from the start. Authentication (Phase 7) now splits cleanly in two: Clerk gets you *in*, Google connection gets Gmail/Calendar *working* — keep that split visible in the UI (separate prompts, separate states, separate failure modes) exactly as it's kept separate in the backend.

*End of Document.*
