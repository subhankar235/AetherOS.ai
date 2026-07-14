
# TECH_STACK.md

# AI Email Assistant — Technology Stack

## Overview

The AI Email Assistant is built using a modern AI-native architecture that combines Large Language Models (LLMs), multi-agent orchestration, Retrieval-Augmented Generation (RAG), real-time communication, and Google Workspace integrations. The system is modular, scalable, and designed to allow future agents and integrations to be added with minimal changes.

---

# Architecture

```
Frontend (Next.js)
        │
        ▼
FastAPI Backend
        │
        ▼
LangGraph Supervisor
        │
 ┌──────┼────────┬────────┬─────────┬──────────┐
 ▼      ▼        ▼        ▼         ▼
Inbox  Reply  Calendar Knowledge Research
Agent  Agent    Agent     Agent      Agent
```

---

# Frontend

| Technology      | Purpose                 |
| --------------- | ----------------------- |
| Next.js 15      | React framework         |
| React 19        | UI development          |
| TypeScript      | Type safety             |
| Tailwind CSS    | Styling                 |
| shadcn/ui       | Component library       |
| Framer Motion   | Animations              |
| TanStack Query  | Server state management |
| Zustand         | Client state management |
| React Hook Form | Forms                   |
| Zod             | Validation              |

---

# Backend

| Technology | Purpose              |
| ---------- | -------------------- |
| FastAPI    | REST API             |
| Python     | Backend language     |
| Uvicorn    | ASGI server          |
| Celery     | Background jobs      |
| Redis      | Task queue & caching |
| WebSockets | Real-time updates    |

---

# Artificial Intelligence

| Technology | Purpose                   |
| ---------- | ------------------------- |
| GPT-5.5    | Primary reasoning model   |
| LangGraph  | Multi-agent orchestration |
| LangChain  | Tool calling & RAG        |
| LangSmith  | Observability & debugging |

---

# Voice AI

| Technology                | Purpose                 |
| ------------------------- | ----------------------- |
| ElevenLabs Speech-to-Text | Voice transcription     |
| ElevenLabs Text-to-Speech | Natural voice responses |

---

# Knowledge Base (RAG)

| Technology                    | Purpose               |
| ----------------------------- | --------------------- |
| Qdrant                        | Vector database       |
| OpenAI text-embedding-3-large | Embedding generation  |
| Unstructured                  | Document parsing      |
| PyMuPDF                       | PDF extraction        |
| DOCX Parser                   | Word document parsing |
| Text Splitter                 | Chunking documents    |

Supported formats:

* PDF
* DOCX
* TXT
* Markdown

---

# Database

## PostgreSQL

Stores:

* Users
* Email metadata
* Playbooks
* VIP contacts
* User settings
* OAuth tokens
* Conversation history
* Agent logs

---

# Cache

## Redis

Used for:

* Session cache
* Conversation memory
* Background queues
* Dashboard cache
* Rate limiting
* Temporary AI context

---

# Authentication

* Google OAuth 2.0
* Clerk (or Auth.js)

---

# Google Workspace Integrations

## Gmail API

Used for:

* Read emails
* Send emails
* Draft emails
* Search emails
* Labels
* Threads
* Attachments

---

## Google Calendar API

Used for:

* Read calendar
* Check availability
* Create events
* Update meetings
* Delete meetings

---

## Google Meet

Used for:

* Generate Meet links
* Attach Meet links to calendar events

---

# AI Agents

## 1. Supervisor Agent

### Responsibilities

* Understand user intent
* Route requests
* Coordinate all agents
* Maintain conversation state

### Stack

* LangGraph
* GPT-5.5
* LangSmith

---

## 2. Inbox Agent

### Responsibilities

* Fetch Gmail
* Categorize emails
* Priority scoring
* Summaries
* Sentiment analysis
* Detect meetings
* Detect follow-ups

### Stack

* Gmail API
* GPT-5.5
* LangGraph

---

## 3. Reply Agent

### Responsibilities

* Read email thread
* Retrieve knowledge
* Apply playbooks
* Draft replies
* Rewrite drafts
* Improve tone
* Send after approval

### Stack

* GPT-5.5
* LangGraph
* Gmail API
* Qdrant

---

## 4. Calendar Agent

### Responsibilities

* Read calendar
* Find free slots
* Generate Meet links
* Create meetings
* Send invitations

### Stack

* Google Calendar API
* Google Meet API

---

## 5. Knowledge Agent

### Responsibilities

* Search uploaded documents
* Retrieve context
* Supply context to Reply Agent

### Stack

* Qdrant
* OpenAI Embeddings
* LangChain
* Unstructured
* PyMuPDF

---

## 6. Research Agent

### Responsibilities

* Company research
* Competitor analysis
* Latest news
* Products
* Pricing
* Customer sentiment
* SWOT analysis

### Stack

* Tavily
* Firecrawl
* Brave Search (or Serper)
* Playwright (optional)
* GPT-5.5
* Qdrant (research cache)

---

## 7. Payment Agent (Future)

### Responsibilities

* Detect invoices
* Extract invoice details
* Vendor verification
* Purchase order matching
* Company policy validation
* Fraud detection
* Payment preparation
* Approval workflow

### Stack

* GPT-5.5
* OCR Engine
* Policy Engine
* ERP Integration APIs
* Stripe / Razorpay / Bank APIs
* PostgreSQL

---

## 8. Support Agent

### Responsibilities

* Product help
* Onboarding
* FAQ
* Documentation search

### Stack

* GPT-5.5
* LangGraph
* Qdrant

---

# Feature-wise Tech Stack

## AI Inbox

### Technologies

* Gmail API
* GPT-5.5
* LangGraph
* PostgreSQL

### Workflow

```
Email Received
      ↓
Gmail API
      ↓
Inbox Agent
      ↓
GPT-5.5
      ↓
Priority
Category
Summary
Action
Urgency
      ↓
Database
      ↓
Dashboard
```

---

## AI Dashboard

### Technologies

* Next.js
* TanStack Query
* WebSockets
* Redis

### Workflow

```
Database Changes
      ↓
Redis
      ↓
WebSocket
      ↓
Dashboard Refresh
```

---

## Voice Assistant

### Technologies

* ElevenLabs STT
* GPT-5.5
* LangGraph
* ElevenLabs TTS

### Workflow

```
Voice
   ↓
Speech-to-Text
   ↓
Supervisor Agent
   ↓
Selected Agent
   ↓
GPT-5.5
   ↓
Text-to-Speech
   ↓
Voice Response
```

---

## Natural Language Search

### Technologies

* GPT-5.5
* Gmail API

### Workflow

```
User Query
      ↓
GPT-5.5
      ↓
Gmail Search Query
      ↓
Gmail API
      ↓
Results
```

---

## AI Reply Generator

### Technologies

* GPT-5.5
* LangGraph
* Gmail API
* Qdrant
* Playbooks

### Workflow

```
User
 ↓
Reply Agent
 ↓
Read Email
 ↓
Knowledge Search
 ↓
Apply Playbook
 ↓
GPT-5.5
 ↓
Draft
 ↓
Approval
 ↓
Send
```

---

## Draft Editing

### Technologies

* GPT-5.5

Features:

* Rewrite
* Grammar correction
* Tone adjustment
* Expand
* Shorten
* Simplify

---

## Meeting Scheduler

### Technologies

* Google Calendar API
* Google Meet API

### Workflow

```
Meeting Request
      ↓
Calendar Agent
      ↓
Availability Check
      ↓
Meet Link
      ↓
Preview
      ↓
Approval
      ↓
Create Event
```

---

## Knowledge Base

### Technologies

* Unstructured
* PyMuPDF
* OpenAI Embeddings
* Qdrant

### Workflow

```
Upload Files
      ↓
Parse
      ↓
Chunk
      ↓
Embeddings
      ↓
Qdrant
      ↓
Semantic Search
      ↓
LLM Context
```

---

## Market Research Agent

### Technologies

* Tavily
* Firecrawl
* Brave Search / Serper
* Playwright (optional)
* GPT-5.5
* Qdrant

### Workflow

```
Research Request
      ↓
Web Search
      ↓
Web Crawling
      ↓
Content Extraction
      ↓
GPT-5.5 Analysis
      ↓
Executive Report
```

---

## Payment Agent

### Technologies

* OCR
* GPT-5.5
* Policy Engine
* Payment APIs

### Workflow

```
Invoice
   ↓
OCR
   ↓
Extract Data
   ↓
Vendor Verification
   ↓
Policy Validation
   ↓
Fraud Check
   ↓
Approval
   ↓
Payment API
```

---

# Monitoring

* LangSmith
* Sentry

---

# Deployment

## Frontend

* Vercel

## Backend

* Google Cloud Run
* Railway (alternative)
* Render (alternative)

## Containerization

* Docker

---

# Security

* Google OAuth 2.0
* HTTPS/TLS
* Encrypted OAuth tokens
* User approval before critical actions
* Secure document storage
* Principle of least privilege for agent permissions

---

# Future Integrations

* Outlook
* Slack
* Microsoft Teams
* Notion
* Salesforce
* HubSpot
* Jira
* GitHub
* Zoom
* Stripe
* Razorpay
* SAP
* Oracle ERP
