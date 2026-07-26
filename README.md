# Aether — AI Chief of Staff for Your Inbox

<p align="center">
  <img src="apps/web/public/logoAether1.png" alt="Aether Logo" width="550"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js"/>
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Gemini-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white" alt="Gemini"/>
  <img src="https://img.shields.io/badge/ElevenLabs-000000?style=for-the-badge&logo=elevenlabs&logoColor=white" alt="ElevenLabs"/>
  <img src="https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white" alt="Google Cloud"/>
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React"/>
  <img src="https://img.shields.io/badge/Chrome-4285F4?style=for-the-badge&logo=googlechrome&logoColor=white" alt="Chrome"/>
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Qdrant-ED1C24?style=for-the-badge&logo=qdrant&logoColor=white" alt="Qdrant"/>
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis"/>
  <img src="https://img.shields.io/badge/LangGraph-1C3C3C?style=for-the-badge&logo=langgraph&logoColor=white" alt="LangGraph"/>
  <img src="https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" alt="LangChain"/>
  <img src="https://img.shields.io/badge/LangSmith-0055FF?style=for-the-badge&logo=langsmith&logoColor=white" alt="LangSmith"/>
  <img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white" alt="Celery"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/Clerk-6C47FF?style=for-the-badge&logo=clerk&logoColor=white" alt="Clerk"/>
  <img src="https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind CSS"/>
  <img src="https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white" alt="Vercel"/>
  <img src="https://img.shields.io/badge/Sentry-362D59?style=for-the-badge&logo=sentry&logoColor=white" alt="Sentry"/>
  <img src="https://img.shields.io/badge/Turborepo-EF4444?style=for-the-badge&logo=turborepo&logoColor=white" alt="Turborepo"/>
  <img src="https://img.shields.io/badge/pnpm-F69220?style=for-the-badge&logo=pnpm&logoColor=white" alt="pnpm"/>
</p>

> Aether is an AI-native, multi-agent executive assistant platform that watches your inbox, triages incoming mail, drafts context-aware replies, schedules meetings, researches companies, and manages business workflows — all through a unified voice or text command interface. Every consequential action is gated behind explicit human approval.

Built for knowledge workers, founders, sales teams, and executive assistants who want the speed of AI automation without losing control.

<p align="center">
  <a href="apps/api/README.md">
    <img src="https://img.shields.io/badge/📖_API_Docs-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="API Docs"/>
  </a>
  <a href="apps/web/README.md">
    <img src="https://img.shields.io/badge/🌐_Web_Docs-000000?style=for-the-badge&logo=next.js&logoColor=white" alt="Web Docs"/>
  </a>
  <a href="apps/extension/README.md">
    <img src="https://img.shields.io/badge/🧩_Extension_Docs-4285F4?style=for-the-badge&logo=googlechrome&logoColor=white" alt="Extension Docs"/>
  </a>
</p>

---

## Features

### AI Command Center
- **Unified input surface** — voice or text, routes to the right AI agent
- **Supervisor Agent** — intent classification, multi-step task decomposition, coreference resolution
- **Real-time conversation** — persistent context across turns, multi-turn edit loops

### Inbox Intelligence
- **Automatic triage** — new emails are fetched, summarized, prioritized, and categorized silently
- **Smart email viewer** — thread summaries, key action items, detected deadlines
- **Natural language search** — plain-English queries translated to Gmail search syntax

### AI Reply Assistant
- **Context-aware drafts** — grounded in thread history + Knowledge Base + Playbooks
- **Iterative editing** — "shorten it," "make it warmer," "add a calendar link"
- **Approval gate** — no email is ever sent without explicit user confirmation

### Calendar Agent
- **Natural language scheduling** — extract dates, times, participants from email or command
- **Availability checking** — free/busy across participants, ranked candidate slots
- **Google Meet integration** — auto-generated meet links with every event proposal

### Knowledge Base (RAG)
- **Company Memory** — upload PDFs, DOCX, TXT, Markdown; auto-chunked, embedded, and stored in Qdrant
- **Semantic search** — queries retrieve relevant facts with source citations
- **Access control** — document-level permissions enforced at query time

### Market Research Agent
- **On-demand company research** — web search + crawling across Tavily, Firecrawl, Serper
- **Structured reports** — Executive Summary, SWOT, Competitors, Opportunities, Risks
- **Per-claim timestamps** — recency of each data point is transparent

### Playbooks
- **Templated reply workflows** — Interview Workflow, Sales Workflow, Customer Support, etc.
- **Automatic scenario matching** — Playbook structure/tone applied when relevant

### Voice Interface
- **ElevenLabs STT/TTS** — low-latency streaming speech transcription and natural voice synthesis
- **Conversational rewrite** — structured results rephrased as natural spoken sentences
- **Tone adaptation** — casual for daily triage, careful for approvals, calm for fraud/suspicious

### Chrome Extension
- **Side panel** — access Aether from any browser tab
- **Cross-device** — independent session context, shared user data
- **Same backend** — zero backend changes needed

### Approval Gate
- **Hard enforcement** — send/schedule/pay actions require explicit approval record
- **Backend-enforced** — not just a UI convention; API routers validate approvals
- **Audit trail** — every consequential action logged with approval metadata

---

## Tech Stack

### Frontend

| Technology | Purpose |
|---|---|
| Next.js 16 (App Router) | React framework |
| React 19 | UI library |
| TypeScript | Type safety |
| Tailwind CSS 4 | Styling |
| shadcn/ui | Component primitives |
| Framer Motion | Animations |
| TanStack Query | Server state management |
| Zustand | Client state management |
| React Hook Form + Zod | Forms and validation |
| Lucide React | Icons |
| Recharts | Charts |

### Backend

| Technology | Purpose |
|---|---|
| FastAPI | REST API framework |
| Python 3.12+ | Backend language |
| Uvicorn | ASGI server |
| SQLAlchemy Async | ORM |
| Alembic | Database migrations |
| Celery | Background job processing |
| Redis | Caching, queues, session store |
| WebSockets | Real-time dashboard updates |
| PostgreSQL | Primary database |
| Qdrant | Vector database |

### AI & Agents

| Technology | Purpose |
|---|---|
| LangGraph | Multi-agent orchestration (state graph) |
| LangChain | Tool calling and RAG |
| LangSmith | Observability and debugging |
| GPT-5.5 / OpenRouter | Primary reasoning model (provider-agnostic) |
| Groq (Llama 3.3 70B) | Fallback LLM provider |
| Gemini 2.5 Flash | Fallback LLM provider |
| OpenAI text-embedding-3-large | Embedding generation |
| Unstructured / PyMuPDF / DOCX Parser | Document parsing |

### Voice

| Technology | Purpose |
|---|---|
| ElevenLabs Speech-to-Text | Voice transcription |
| ElevenLabs Text-to-Speech | Natural voice synthesis |

### Authentication & Integrations

| Technology | Purpose |
|---|---|
| Clerk | User identity, session management, JWT |
| Google OAuth 2.0 | Gmail/Calendar/Meet API access (separate from auth) |
| Gmail API | Read, send, search, draft emails |
| Google Calendar API | Read calendar, check availability, create events |
| Google Meet API | Video conference link generation |

### Search & Research

| Technology | Purpose |
|---|---|
| Tavily | Web search (Market Research Agent) |
| Firecrawl | Web crawling and structured extraction |
| Brave Search / Serper | Web search provider |

### Infrastructure

| Technology | Purpose |
|---|---|
| Docker | Containerization |
| Docker Compose | Local development (Postgres, Redis, Qdrant) |
| Turborepo | Monorepo orchestration |
| pnpm | Package manager |
| Sentry | Error tracking |
| Vercel | Frontend deployment target |
| Google Cloud Run | Backend deployment target |

### Dev Tools

| Technology | Purpose |
|---|---|
| Prettier | Code formatting |
| ESLint | Linting |
| EditorConfig | Editor consistency |
| Pydantic | Data validation (backend) |
| Tenacity | Retry/backoff for external API calls |

---

## Architecture Overview

### System Architecture

```mermaid
flowchart TB
    classDef client fill:#60a5fa,stroke:#2563eb,color:#fff
    classDef webApp fill:#a78bfa,stroke:#7c3aed,color:#fff
    classDef apiApp fill:#34d399,stroke:#059669,color:#000
    classDef agent fill:#fbbf24,stroke:#d97706,color:#000
    classDef infra fill:#f472b6,stroke:#db2777,color:#fff
    classDef external fill:#94a3b8,stroke:#475569,color:#fff
    classDef auth fill:#fde047,stroke:#a16207,color:#000

    %% ── Clients ──
    subgraph CLIENTS["Clients"]
        direction LR
        BROWSER["Web Browser"]:::client
        EXT["Chrome Extension"]:::client
    end

    %% ── Frontend Layer ──
    subgraph FRONTEND["Frontend – Next.js 16"]
        WEB["Aether Web App<br/>apps/web"]:::webApp
        WEB_COMP["Shared UI Components<br/>shadcn/ui · Tailwind 4"]:::webApp
        WEB_STATE["State Stores<br/>TanStack Query · Zustand"]:::webApp
    end

    %% ── Backend Layer ──
    subgraph BACKEND["Backend – FastAPI on Google Cloud Run"]
        API["API Gateway<br/>apps/api/main.py"]:::apiApp
        MIDDLEWARE["Middleware Stack<br/>CORS · Clerk Auth · Rate Limit · Logging"]:::apiApp
        ROUTERS["Routers<br/>command_center · inbox · replies · calendar<br/>knowledge · research · dashboard · payments"]:::apiApp

        subgraph AGENTS["LangGraph Multi-Agent System"]
            direction LR
            SUP["Supervisor Agent<br/>Intent · Decompose · Route"]:::agent
            INBOX["Inbox<br/>Agent"]:::agent
            REPLY["Reply<br/>Agent"]:::agent
            CAL["Calendar<br/>Agent"]:::agent
            KNOW["Knowledge<br/>Agent"]:::agent
            RESEARCH["Research<br/>Agent"]:::agent
            SUPP["Support<br/>Agent"]:::agent
        end

        APPROVAL["Approval Gate<br/>API-enforced · Audit Trail"]:::agent
    end

    %% ── Infrastructure ──
    subgraph INFRA["Infrastructure – Docker Compose / Cloud"]
        PG[("PostgreSQL<br/>Primary Store")]:::infra
        QDRANT[("Qdrant<br/>Vector Store")]:::infra
        REDIS[("Redis<br/>Cache · Queue · Pub/Sub")]:::infra
        WORKERS["Celery Workers<br/>email_processor · kb_indexer<br/>research_cache_refresh"]:::infra
    end

    %% ── External Services ──
    subgraph EXTERNAL["External Services"]
        CLERK["Clerk<br/>Auth & Identity"]:::auth
        GOOGLE["Google APIs<br/>Gmail · Calendar · Meet"]:::external
        ELEVEN["ElevenLabs<br/>STT · TTS · Voice"]:::external
        LLM["LLM Providers<br/>OpenRouter · Groq · Gemini"]:::external
        SEARCH["Search Providers<br/>Tavily · Firecrawl · Serper"]:::external
    end

    %% ── Connections ──
    BROWSER -->|HTTPS · REST · WebSocket| WEB
    EXT -->|HTTPS · REST · WebSocket| WEB
    WEB -->|REST API :8000| API
    EXT -->|REST API :8000| API
    API --> MIDDLEWARE
    MIDDLEWARE --> ROUTERS
    ROUTERS --> SUP
    SUP --> INBOX & REPLY & CAL & KNOW & RESEARCH & SUPP
    INBOX & REPLY & CAL & KNOW & RESEARCH & SUPP --> APPROVAL
    APPROVAL --> PG
    APPROVAL --> REDIS
    AGENTS --> QDRANT
    AGENTS --> WORKERS
    WORKERS --> PG
    WORKERS --> REDIS
    WORKERS --> QDRANT
    API -->|JWT validation| CLERK
    AGENTS -->|REST API calls| GOOGLE
    AGENTS -->|API calls| ELEVEN
    AGENTS -->|LLM inference| LLM
    AGENTS -->|Web search| SEARCH
```

### Service Communication & Data Flow

```mermaid
flowchart LR
    classDef web fill:#a78bfa,stroke:#7c3aed,color:#fff
    classDef api fill:#34d399,stroke:#059669,color:#000
    classDef data fill:#f472b6,stroke:#db2777,color:#fff
    classDef async fill:#fbbf24,stroke:#d97706,color:#000
    classDef svc fill:#60a5fa,stroke:#2563eb,color:#fff

    %% Services
    WEB["Next.js Web App<br/>apps/web"]:::web
    API["FastAPI Backend<br/>apps/api"]:::api
    PG[("PostgreSQL<br/>:5433")]:::data
    QDRANT[("Qdrant Vector DB<br/>:6333")]:::data
    REDIS[("Redis<br/>:6379")]:::async
    CELERY["Celery Workers"]:::async
    WS["WebSocket Server<br/>/ws"]:::async

    %% External
    CLERK["Clerk Auth"]:::svc
    GOOGLE["Google APIs"]:::svc
    LLM["LLM Providers"]:::svc
    ELEVEN["ElevenLabs"]:::svc

    %% ── Request Path (REST) ──
    WEB == "REST :8000" ==> API
    API -->|SQLAlchemy| PG
    API -->|Redis Cache| REDIS
    API -->|Qdrant Client| QDRANT
    API -->|Celery Task Queue| REDIS
    REDIS -->|Celery Worker| CELERY
    CELERY -->|Read/Write| PG
    CELERY -->|Read/Write| QDRANT

    %% ── WebSocket (real-time) ──
    WEB <==>|WebSocket :8000/ws| WS
    WS -.->|broadcast| WEB
    API -.->|publish| WS

    %% ── External ──
    API -->|JWT Verify| CLERK
    API -->|OAuth 2.0| GOOGLE
    API -->|OpenAI SDK| LLM
    API -->|REST| ELEVEN

    %% ── Edge / Cache Flow ──
    PG ---|"Row-Level Security"| API
    QDRANT ---|"per-org access filter"| API
    REDIS ---|"session · rate-limit · pub/sub"| API
```

### Request Flow

1. **User input** — voice (ElevenLabs STT) or text via Command Center
2. **Supervisor Agent** — classifies intent, resolves references ("it", "the first one"), decomposes multi-step tasks
3. **Specialized Agent** — instantiated on-demand per task (Inbox, Reply, Calendar, Knowledge, Research, Support)
4. **Execution** — agent reads/writes via integrations (Gmail API, Calendar API, Qdrant, Google Search)
5. **Approval Gate** — if action is consequential (send/schedule/pay), approval record is created; endpoint blocks execution without valid approval
6. **Response** — result returned to Supervisor, rendered in UI; voice mode: conversational rewrite → ElevenLabs TTS
7. **Agent terminates** — only Supervisor persists across turns

### Automatic Flow (only 4 things)
- **Fetch** new email via Gmail Pub/Sub webhook
- **Summarize** body into 1–2 sentences via LLM
- **Prioritize** as High/Medium/Low
- **Categorize** (Sales, Support, Internal, Newsletter, etc.)

Everything else requires an explicit user command.

---

## Project Structure

```
aether/
├── apps/
│   ├── api/                      # FastAPI backend → [Detailed API docs](apps/api/README.md)
│   │   ├── agents/               # LangGraph multi-agent system
│   │   │   ├── supervisor/       # Intent router, context manager, task decomposer
│   │   │   ├── inbox_agent/      # Email sync, search, reader
│   │   │   ├── reply_agent/      # Draft, edit, send (with approval)
│   │   │   ├── calendar_agent/   # Extract, availability, event creator
│   │   │   ├── knowledge_agent/  # RAG retrieval, document indexing
│   │   │   ├── research_agent/   # Web search, crawl, synthesis
│   │   │   ├── support_agent/    # Product help, FAQ
│   │   │   └── payment_agent/    # Scaffolded (future)
│   │   ├── core/                 # Config, security, exceptions, logging
│   │   ├── db/                   # SQLAlchemy session, Alembic migrations
│   │   ├── integrations/         # Gmail, Calendar, Meet, Qdrant, search providers
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── routers/              # FastAPI route handlers
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── services/             # Ingestion, RAG, approval gate, audit
│   │   ├── voice/                # STT, TTS, conversational rewrite
│   │   ├── websocket/            # Connection manager, event broadcasting
│   │   └── workers/              # Celery background tasks
│   │
│   ├── web/                      # Next.js 16 frontend → [Detailed frontend docs](apps/web/README.md)
│   │   ├── app/                  # App Router pages
│   │   │   ├── (app)/dashboard/  # Inbox overview with live stats
│   │   │   ├── (app)/inbox/      # Email list and detail view
│   │   │   ├── (app)/command/    # AI Command Center (voice + text)
│   │   │   ├── (app)/calendar/   # Calendar agent proposals
│   │   │   ├── (app)/replies/    # Reply drafts
│   │   │   ├── (app)/knowledge/  # Knowledge Base management
│   │   │   ├── (app)/research/   # Market research reports
│   │   │   ├── (app)/approvals/  # Unified approval queue
│   │   │   ├── (app)/settings/   # User preferences, integrations
│   │   │   ├── (app)/payments/   # Payment Agent (future)
│   │   │   └── (auth)/           # Sign-in / Sign-up (Clerk)
│   │   ├── components/           # UI components
│   │   │   ├── ui/               # shadcn/ui primitives
│   │   │   ├── landing/          # Marketing site sections
│   │   │   └── layout/           # App sidebar, shell
│   │   ├── hooks/                # React hooks
│   │   ├── stores/               # Zustand state stores
│   │   └── lib/                  # API client, mock data, utilities
│   │
│   └── extension/                # Chrome Extension (MV3) → [Extension docs](apps/extension/README.md)
│       ├── src/
│       │   ├── background/       # Service worker
│       │   ├── sidepanel/        # React side panel UI
│       │   ├── lib/              # API client, WebSocket, auth, stores
│       │   └── utils/            # Audio utilities
│       └── public/               # Icons, manifest
│
├── packages/                     # Shared monorepo packages
│   ├── types/                    # Shared TypeScript type definitions
│   ├── constants/                # Shared enums and constants
│   └── config/                   # Shared environment schemas
│
├── Docs/                         # Project documentation
│   ├── PRD.md                    # Product Requirements Document
│   ├── techstack.md              # Technology stack reference
│   ├── workflow.md               # User workflow diagrams
│   ├── steps-backend.md          # Backend implementation roadmap
│   ├── steps-frontend.md         # Frontend implementation roadmap
│   ├── chrome-extention.md       # Chrome Extension build guide
│   └── file-structure.md         # Detailed folder mapping
│
├── docker-compose.yml            # Local dev infrastructure (Postgres, Redis, Qdrant)
├── turbo.json                    # Turborepo pipeline configuration
├── pnpm-workspace.yaml           # pnpm workspace definition
└── .env.example                  # Environment variable template
```

---

## How It Works

### Daily Triage Flow

1. User opens the app → Dashboard shows new email count, high-priority count, categories
2. User says: *"Read me the high-priority ones"*
3. Inbox Agent surfaces 3 emails with AI summaries; TTS reads them aloud
4. User says: *"Reply to the investor one, keep it warm but concise"*
5. Reply Agent drafts an email grounded in Knowledge Base + thread context + matching Playbook
6. User reviews, says *"shorten it"*, reviews again
7. User says *"send it"* → confirmation screen → user approves → email sent via Gmail API
8. Total elapsed time: ~3 minutes

### First-Time Setup

1. Sign in via Clerk (email/password, Google social login, or magic link)
2. Connect Google account (Gmail + Calendar scopes) — separate from login, happens in Settings
3. Dashboard loads with async historical inbox backfill
4. Guided tutorial: *"Try saying: show me my unread emails"*

### Context Resolution

The Supervisor Agent maintains short-term conversational context in Redis (keyed by user session). References like "it," "the first one," or "that meeting" are resolved against the last search results, active draft, or active calendar preview. Context persists across devices (server-side per user session) with a 30-minute inactivity TTL.

---

## Installation

### Prerequisites

- Node.js 20+
- Python 3.12+
- pnpm 9+
- Docker + Docker Compose
- Clerk account
- Google Cloud Console project (Gmail API, Calendar API enabled)
- OpenAI API key (or OpenRouter key)
- ElevenLabs API key
- Qdrant instance (local via Docker or cloud)

### Clone and Install

```bash
git clone <repo-url>
cd aether

# Install frontend dependencies
pnpm install

# Set up Python backend
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ../..
```

### Environment Setup

```bash
cp .env.example .env
# Edit .env with your actual API keys and secrets
```

### Start Infrastructure

```bash
docker-compose up -d
# Starts PostgreSQL (port 5433), Redis (6379), Qdrant (6333)
```

### Database Setup

```bash
cd apps/api
alembic upgrade head
```

### Start Development

```bash
# Start all apps concurrently
pnpm dev

# Or start individually:
cd apps/api && uvicorn main:app --reload  # Backend on :8000
cd apps/web && pnpm dev                    # Frontend on :3000
```

---

## Environment Variables

| Variable | Purpose | Required | Default |
|---|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | Yes | `postgresql+asyncpg://postgres:postgres@localhost:5432/ai_email_assistant` |
| `REDIS_URL` | Redis connection string | Yes | `redis://localhost:6379/0` |
| `QDRANT_URL` | Qdrant vector DB URL | Yes | `http://localhost:6333` |
| `OPENAI_API_KEY` | Primary LLM provider API key | Yes | — |
| `GROQ_API_KEY` | Fallback LLM provider | No | — |
| `GEMINI_API_KEY` | Fallback LLM provider | No | — |
| `LLM_FALLBACK_ORDER` | Provider priority order | No | `openrouter,groq,gemini` |
| `ELEVENLABS_API_KEY` | Voice STT/TTS | Yes | — |
| `GOOGLE_OAUTH_CLIENT_ID` | Google API integration OAuth | Yes | — |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google API integration OAuth | Yes | — |
| `CLERK_SECRET_KEY` | Clerk backend auth | Yes | — |
| `CLERK_PUBLISHABLE_KEY` | Clerk frontend auth | Yes | — |
| `CLERK_WEBHOOK_SIGNING_SECRET` | Clerk webhook verification | Yes | — |
| `JWT_SECRET` | Token encryption key | Yes | — |
| `TAVILY_API_KEY` | Web search (Research Agent) | No | — |
| `FIRECRAWL_API_KEY` | Web crawling (Research Agent) | No | — |
| `SERPER_API_KEY` | Web search (Research Agent) | No | — |
| `SENTRY_DSN` | Error tracking (backend) | No | — |
| `LANGSMITH_API_KEY` | LangSmith observability | No | — |
| `NEXT_PUBLIC_API_URL` | Frontend → Backend API URL | Yes | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | Frontend → Backend WebSocket URL | Yes | `ws://localhost:8000/ws` |
| `NEXT_PUBLIC_SENTRY_DSN` | Error tracking (frontend) | No | — |

---

## Available Scripts

| Script | Description |
|---|---|
| `pnpm dev` | Start all apps in development mode (via Turborepo) |
| `pnpm build` | Build all apps for production |
| `pnpm lint` | Run ESLint across the workspace |
| `pnpm format` | Format code with Prettier |
| `pnpm clean` | Clean build artifacts |

### Backend (apps/api)

| Script | Description |
|---|---|
| `uvicorn main:app --reload` | Start FastAPI dev server |
| `alembic upgrade head` | Run database migrations |
| `python -m pytest` | Run backend tests |

### Frontend (apps/web)

| Script | Description |
|---|---|
| `pnpm dev` | Start Next.js dev server |
| `pnpm build` | Build for production |
| `pnpm start` | Start production server |

### Extension (apps/extension)

| Script | Description |
|---|---|
| `pnpm dev` | Start Vite dev server |
| `pnpm build` | Build extension for Chrome |
| `pnpm preview` | Preview production build |

---

## API Overview

Key API endpoints (grouped by feature):

### Command Center
- `POST /command` — Execute a text command through the Supervisor Agent
- `POST /command/voice` — Execute a voice command (audio upload → STT → Supervisor)

### Inbox
- `GET /inbox/emails` — List indexed emails (prioritized, categorized)
- `GET /inbox/search` — Natural language search (translated to Gmail query)
- `GET /inbox/recent` — Sync and fetch recent emails from Gmail API

### Replies
- `POST /replies/drafts` — Generate a reply draft for a given email
- `GET /replies/drafts` — List active drafts
- `POST /replies/drafts/{id}/edit` — Edit a draft with instructions
- `POST /replies/drafts/{id}/prepare-send` — Prepare send (creates approval request)
- `POST /replies/drafts/{id}/send` — Execute send (requires valid approval)

### Calendar
- `POST /calendar/extract` — Extract meeting details from natural language
- `POST /calendar/availability` — Check free/busy slots across participants
- `POST /calendar/preview` — Create meeting proposal preview
- `POST /calendar/confirm` — Confirm and create calendar event (requires approval)
- `GET /calendar/meetings` — List meeting proposals

### Dashboard
- `GET /dashboard/summary` — Aggregate inbox stats (total, high priority, pending approvals)

### Knowledge Base
- `POST /knowledge/query` — Semantic search across Company Memory
- `POST /knowledge/documents` — Upload a document for indexing

### Integrations
- `GET /integrations/google/status` — Check Google connection status
- `GET /integrations/google/connect` — Start Google OAuth flow
- `DELETE /integrations/google` — Disconnect Google integration

### WebSocket
- `GET /ws` — Real-time dashboard updates (new emails, draft changes, approvals)

### Webhooks
- `POST /webhooks/clerk` — Clerk user lifecycle events (created/updated/deleted)
- `POST /webhooks/gmail` — Gmail Pub/Sub push notifications for new emails

---

## Database

### PostgreSQL (Primary Store)

**Main entities:**

| Entity | Description |
|---|---|
| `users` | User identity, linked to Clerk |
| `google_integrations` | Per-user Google OAuth tokens (encrypted at rest) |
| `email_metadata` | Categorized/summarized email metadata (idempotency keyed by Gmail message ID) |
| `threads` | Email thread summaries |
| `drafts` | AI-generated drafts with version history (JSONB) |
| `meetings` | Calendar meeting proposals and confirmations |
| `knowledge_documents` | Uploaded document tracking and indexing status |
| `playbooks` | Reusable reply templates |
| `vip_contacts` | User-designated priority contacts |
| `agent_logs` | Audit trail for all agent actions and approvals |
| `conversation_context` | Durable backstop for session context |

**Row-level security (RLS)** is enabled on all user-scoped tables as defense-in-depth against cross-tenant data access.

### Qdrant (Vector Store)

| Collection | Purpose |
|---|---|
| `company_memory` | Document chunks for RAG (per-org, access-controlled) |
| `research_cache` | Cached market research reports (TTL-based) |
| `support_kb` | Product documentation for the Support Agent |

### Redis (Cache & Ephemeral State)

- Session context (30-minute TTL)
- Dashboard cache (aggregated counts)
- Celery task queues
- Rate limiting counters per user per integration

---

## Authentication

Aether uses **Clerk** for user identity and session management. Google OAuth 2.0 is used **only** as a per-user integration connection (Gmail/Calendar API access) — it is not used for login. These are two independent concerns:

| Layer | Provider | Purpose |
|---|---|---|
| Login / Identity | Clerk | Who you are, session management |
| Integration | Google OAuth 2.0 | Gmail/Calendar/Meet API access |

- Clerk handles sign-in, sign-up, session refresh, MFA, and social login
- Google integration is established post-login via Settings → Integrations
- A disconnected Google account does not log the user out
- Clerk session JWTs are verified against Clerk's JWKS on every API request

---

## Authorization

- **Roles:** Owner, Admin, Member, Viewer (scaffolded for future team workspaces)
- **Agent-level:** Each agent has least-privilege access to integrations (e.g., Knowledge Agent cannot send email)
- **Document-level:** Knowledge Base documents are filtered by `org_id` and `access_level` at query time
- **Approval Gate:** Consequential actions (send, schedule) require a valid approval record — enforced at the API layer, not the UI

---

## AI Features

### Multi-Agent Architecture (LangGraph)

The system uses a **Supervisor Agent** (always running) that orchestrates **specialized agents** (instantiated on-demand, terminate after response):

| Agent | Responsibility | Lifecycle |
|---|---|---|
| **Supervisor** | Intent classification, context management, orchestration | Persistent per session |
| **Inbox Agent** | Email sync, summarization, search, read | Auto-pipeline (continuous) + on-demand |
| **Reply Agent** | Draft generation, editing, send | Per reply session (multi-turn) |
| **Calendar Agent** | Meeting scheduling, availability | Per scheduling session |
| **Knowledge Agent** | RAG retrieval, Company Memory query | Per query (stateless) |
| **Research Agent** | Web research, structured reports | Per research command |
| **Support Agent** | Product help, onboarding | Per help request |
| **Payment Agent** | (Future — scaffolded) | Per payment workflow |

### Agent Communication Contract

All agents communicate via a standard envelope:
```json
{
  "agent": "reply_agent",
  "status": "waiting_for_user | completed | error | clarification_needed",
  "result": { "...task-specific..." },
  "context_updates": { "active_draft_id": "..." },
  "requires_approval": true
}
```

### RAG Pipeline

1. **Ingestion:** Upload → parse (PDF/DOCX/TXT/MD) → chunk (~300-500 tokens) → embed (OpenAI text-embedding-3-large) → store in Qdrant with metadata
2. **Retrieval:** Query → embed → Qdrant `top-k` similarity search (with `org_id` + `access_level` filter) → optional reranking → return chunks + citations

### LLM Provider Failover

The system supports multiple LLM providers with automatic fallback:
- Default order: `openrouter` → `groq` → `gemini`
- Configured via `LLM_FALLBACK_ORDER` environment variable
- If one provider fails, the next in line is tried automatically
- Model tiering: cheaper/faster model for classification, premium model for generation

---

## Background Jobs

Celery workers handle asynchronous processing:

| Worker | Purpose |
|---|---|
| `email_processor` | Processes new email notifications from Gmail Pub/Sub (fetch → summarize → categorize → store) |
| `kb_indexer` | Indexes uploaded documents (parse → chunk → embed → store in Qdrant) |
| `research_cache_refresh` | Periodic cache cleanup for stale research reports |
| `invoice_scanner` | (Scaffolded) Background invoice detection for future Payment Agent |

---

## Deployment

### Docker Compose (Local Development)

```bash
docker-compose up -d
# Starts Postgres, Redis, Qdrant
```

### Production

- **Frontend:** Deployed to Vercel
- **Backend:** Deployed to Google Cloud Run (or Railway, Render)
- **Infrastructure:** Managed PostgreSQL (Cloud SQL), Redis (Memorystore), Qdrant Cloud
- **Containerization:** Docker for both API and web services

### CI/CD

Configuration for GitHub Actions is outlined in the project documentation:
- `deploy-api.yml` — Build and deploy backend to Cloud Run
- `deploy-web.yml` — Build and deploy frontend to Vercel
- `run-tests.yml` — Run test suite on PRs

---

## Security

- **Authentication:** Clerk session JWTs verified via RS256 against Clerk's JWKS
- **Token encryption:** Google OAuth tokens encrypted at rest using AES-256-GCM
- **Approval gate:** Every send/schedule action requires explicit backend-enforced approval — bypassing the UI is impossible
- **Prompt injection defense:** All agents treat email/document content as data, never instructions (system-level guardrails)
- **Least privilege:** Agent access to integrations is restricted per-agent (no agent has capabilities it doesn't need)
- **Row-level security:** PostgreSQL RLS policies on all user-scoped tables (defense-in-depth)
- **Qdrant access filtering:** Every vector search is filtered by `org_id` and `access_level` server-side
- **Webhook verification:** Clerk and Gmail webhooks validated via HMAC/signature verification
- **CORS:** Locked to known frontend origins in production
- **Rate limiting:** Per-user, per-integration rate limits enforced via Redis

---

## Performance Optimizations

- **Model tiering:** Cheaper/faster models for classification tasks; premium models for generation
- **Caching:** Dashboard stats, session context, and research reports cached in Redis/Qdrant with TTL
- **Background processing:** Email ingestion and document indexing offloaded to Celery workers
- **Streaming:** Voice transcription streams for low-latency partial results; TTS audio streamed to client
- **WebSocket push** — real-time dashboard updates without polling
- **Structured output** — LLM responses use JSON mode for reliable parsing (no regex on free text)
- **Idempotency** — Gmail message IDs prevent duplicate email processing

---

## Error Handling

- **Hierarchical exceptions:** `AppError` → `AuthError`, `NotFoundError`, `ValidationError`, `IntegrationAuthRequiredError`, `ApprovalRequiredError`, `ExternalServiceError`, `RateLimitError`
- **Consistent JSON error envelope:** `{ "error": { "code", "message", "request_id", "details" } }`
- **LLM failover:** If one provider fails, the next configured provider is tried automatically
- **Graceful degradation:** Health endpoint reports individual dependency status (DB/Redis/Qdrant)
- **Retry with backoff:** External API calls wrapped in Tenacity retry decorator (3 attempts, exponential backoff)

---

## Logging

- **Structured JSON logging** — every log line includes `request_id`, `user_id`, `agent_name`
- **LangSmith** — full request tracing across Supervisor → Agent → Tool calls for debugging and optimization
- **Sentry** — error tracking for both backend and frontend
- **Audit logs** — every consequential action logged with agent name, action type, input/output payloads (redacted), approval status

---

## Development Guidelines

### Conventions

- **Monorepo:** Turborepo + pnpm workspaces (`apps/*`, `packages/*`)
- **Backend:** Python 3.12+, async throughout, FastAPI, SQLAlchemy async, Pydantic schemas
- **Frontend:** Next.js 16 App Router, TypeScript, Tailwind CSS 4, `"use client"` for interactive components
- **Agents:** LangGraph state graph with typed state, strict input/output schemas per agent
- **API Design:** RESTful with consistent error envelopes; WebSocket for real-time events
- **Database:** SQLAlchemy async ORM + Alembic migrations; RLS enabled on user-scoped tables
- **Formatting:** Prettier (no semicolons, single quotes, trailing commas)
- **Editor:** EditorConfig (2-space indent for JS/TS, 4-space for Python)

### Architecture Rules

1. **Only 4 automatic operations:** fetch, summarize, prioritize, categorize — no agent sends/schedules/pays without explicit user command
2. **Supervisor is the only long-lived agent** — specialized agents instantiated per-task, terminate after response
3. **`requires_approval: true` enforced at API layer** — backend blocks unapproved actions regardless of UI
4. **Email content is untrusted data** — never treated as instructions
5. **Least-privilege tool access** — enforced per-agent via import boundaries
6. **Structured output** — anything parsed by code uses JSON mode / function calling
7. **Identity and integration are separate** — Clerk for login, Google OAuth for API access

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `Clerk secret key not configured` | Set `CLERK_SECRET_KEY`, `CLERK_PUBLISHABLE_KEY`, `CLERK_WEBHOOK_SIGNING_SECRET` in `.env` |
| `Google integration not connected` | Go to Settings → Integrations → Connect Google |
| `No emails appearing` | Issue a command like "show my recent emails" to trigger Gmail sync |
| `LLM call fails` | Check `OPENAI_API_KEY` (or `GROQ_API_KEY`/`GEMINI_API_KEY`); verify `LLM_FALLBACK_ORDER` |
| `Database migration fails` | Run `alembic upgrade head` from `apps/api/` |
| `Extension won't load` | Build with `pnpm build` in `apps/extension/`, load unpacked from `dist/` |
| `Voice not working` | Verify `ELEVENLABS_API_KEY` and microphone permissions |
| `Qdrant connection refused` | Ensure Docker Compose is running: `docker-compose up -d` |

---

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Commit your changes:** `git commit -m 'Add amazing feature'`
4. **Push to the branch:** `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Setup

```bash
pnpm install
docker-compose up -d
# Set up .env from .env.example
# Run migrations: alembic upgrade head
pnpm dev
```

### Coding Standards

- Follow existing code patterns (see Development Guidelines)
- Run `pnpm lint` before committing
- Add tests for new features
- Update documentation for API changes

---

## License

This project is licensed under the terms specified in the repository. See the LICENSE file for details. If no license is present, all rights reserved — please contact the maintainers for usage inquiries.

---

## Roadmap

- **Team Workspaces** — shared Company Memory, Playbooks, and multi-user approval workflows
- **Outlook / Microsoft 365** — expand beyond Gmail
- **Slack & Teams** — multi-channel support beyond email
- **Payment Agent** — invoice detection, vendor verification, policy validation, approval-gated payment execution
- **CRM Integration** — Salesforce, HubSpot sync
- **Notion, Jira, GitHub** — knowledge base expansion
- **On-premise deployment** — self-hosted option for enterprise security requirements

---

<div align="center">
  <p><strong>Aether</strong> — Your inbox, autonomously refined.</p>
  <p>
    <a href="https://github.com/subhankar235/Aether">Report a bug</a>
    ·
    <a href="https://github.com/subhankar235/Aether">Request a feature</a>
  </p>
</div>
