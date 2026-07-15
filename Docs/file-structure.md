#ROOT-
ai-email-assistant/
│
├── apps/
│   ├── web/                         # Frontend (Next.js) — detailed structure already given
│   └── api/                         # Backend (FastAPI) — detailed structure already given
│
├── packages/                        # shared code between web & api (optional but recommended)
│   ├── types/                       # shared TypeScript/Pydantic-mirrored types
│   ├── constants/                   # shared enums (priority levels, categories, agent names)
│   └── config/                      # shared env/config schemas
│
├── infra/
│   ├── docker/
│   │   ├── docker-compose.yml       # local dev: postgres, redis, qdrant, api, web
│   │   ├── Dockerfile.api
│   │   └── Dockerfile.web
│   ├── terraform/                   # or equivalent IaC for cloud infra
│   │   ├── modules/
│   │   └── environments/
│   │       ├── dev/
│   │       ├── staging/
│   │       └── production/
│   └── ci-cd/
│       └── github-actions/
│           ├── deploy-api.yml
│           ├── deploy-web.yml
│           └── run-tests.yml
│
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── STRUCTURE.md
│   ├── API_REFERENCE.md
│   └── AGENT_WORKFLOWS.md
│
├── scripts/
│   ├── setup.sh                     # first-time local setup
│   ├── seed_db.py                   # sample data for dev
│   └── migrate.sh
│
├── .github/
│   └── workflows/                   # (if not nested under infra/ci-cd)
│
├── .env.example
├── .gitignore
├── package.json                     # root — turborepo/nx workspace config
├── turbo.json                       # if using Turborepo
├── docker-compose.yml               # top-level shortcut for full local stack
└── README.md






#FRONTEND-
web/
├── package.json
├── next.config.js
├── tailwind.config.ts
│
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── callback/page.tsx
│   │
│   ├── dashboard/
│   │   └── page.tsx                 # includes pending payments widget
│   │
│   ├── inbox/
│   │   ├── page.tsx
│   │   └── [emailId]/page.tsx
│   │
│   ├── knowledge-base/
│   │   └── page.tsx
│   │
│   ├── playbooks/
│   │   └── page.tsx
│   │
│   ├── payments/                    # ⭐ NEW
│   │   ├── page.tsx                 # invoice list (pending/approved/paid)
│   │   ├── [paymentId]/page.tsx     # payment detail + preview
│   │   └── vendors/page.tsx         # manage known vendors
│   │
│   ├── settings/
│   │   ├── page.tsx
│   │   ├── vip-contacts/page.tsx
│   │   └── payment-policy/page.tsx  # ⭐ NEW: thresholds, approver rules
│   │
│   └── layout.tsx                   # mounts persistent Command Center globally
│
├── components/
│   ├── command-center/
│   │   ├── CommandBar.tsx
│   │   ├── AssistantAvatar.tsx
│   │   ├── VoiceVisualizer.tsx
│   │   ├── ConversationThread.tsx
│   │   ├── ApprovalCard.tsx         # generic — reused for send/schedule/PAY
│   │   └── useCommandCenter.ts
│   │
│   ├── voice/
│   │   ├── useMicRecorder.ts
│   │   └── useTextToSpeechPlayer.ts
│   │
│   ├── email/
│   │   ├── EmailListItem.tsx
│   │   ├── EmailViewer.tsx
│   │   └── ThreadView.tsx
│   │
│   ├── agents/
│   │   ├── ReplyDraftCard.tsx
│   │   ├── MeetingPreviewCard.tsx
│   │   ├── ResearchReportCard.tsx
│   │   ├── KnowledgeAnswerCard.tsx
│   │   └── PaymentPreviewCard.tsx   # ⭐ NEW: invoice/vendor/amount/policy check result
│   │
│   ├── payments/                    # ⭐ NEW
│   │   ├── InvoiceListItem.tsx      # status badge: pending/flagged/approved/paid
│   │   ├── InvoiceDetail.tsx        # extracted OCR fields, editable before approval
│   │   ├── FraudWarningBanner.tsx   # shown when vendor/bank details changed
│   │   ├── PolicyCheckBadge.tsx     # pass/fail against payment policy
│   │   └── ApprovalConfirmModal.tsx # final "approve payment" confirmation
│   │
│   ├── dashboard/
│   │   ├── SummaryStats.tsx
│   │   ├── PriorityList.tsx
│   │   └── PendingPaymentsWidget.tsx # ⭐ NEW
│   │
│   └── ui/                          # shadcn/ui primitives
│
├── hooks/
│   ├── useWebSocket.ts
│   ├── useAuth.ts
│   ├── useConversationContext.ts
│   └── usePayments.ts               # ⭐ NEW: fetch/approve/reject invoice
│
├── stores/
│   ├── commandCenterStore.ts
│   ├── inboxStore.ts
│   ├── authStore.ts
│   └── paymentsStore.ts             # ⭐ NEW
│
├── lib/
│   ├── api-client.ts
│   ├── websocket-client.ts
│   └── audio-utils.ts
│
└── styles/
    └── globals.css








#BACKEND-
api/
├── main.py
├── requirements.txt
├── Dockerfile
├── .env.example
│
├── core/
│   ├── config.py
│   ├── security.py
│   ├── logging.py
│   └── exceptions.py
│
├── routers/
│   ├── auth.py
│   ├── dashboard.py
│   ├── inbox.py
│   ├── command_center.py
│   ├── knowledge.py
│   ├── calendar.py
│   ├── research.py
│   ├── playbooks.py
│   ├── vip_contacts.py
│   ├── settings.py
│   └── payments.py                  # ⭐ invoice list, preview, approve, execute endpoints
│
├── websocket/
│   ├── connection_manager.py
│   └── events.py
│
├── agents/
│   ├── supervisor/
│   │   ├── graph.py
│   │   ├── intent_router.py
│   │   ├── context_manager.py
│   │   └── task_decomposer.py
│   │
│   ├── inbox_agent/
│   │   ├── auto_pipeline.py
│   │   ├── search.py
│   │   └── reader.py
│   │
│   ├── reply_agent/
│   │   ├── drafter.py
│   │   ├── editor.py
│   │   └── sender.py
│   │
│   ├── calendar_agent/
│   │   ├── extractor.py
│   │   ├── availability.py
│   │   └── event_creator.py
│   │
│   ├── knowledge_agent/
│   │   ├── retriever.py
│   │   └── indexer.py
│   │
│   ├── research_agent/
│   │   ├── planner.py
│   │   ├── crawler.py
│   │   └── synthesizer.py
│   │
│   ├── support_agent/
│   │   └── help.py
│   │
│   └── payment_agent/               # ⭐⭐ fully built
│       ├── invoice_detector.py      # detects invoice-type emails/attachments
│       ├── ocr_extractor.py         # extracts amount, vendor, due date, invoice #
│       ├── vendor_verifier.py       # checks vendor against known/trusted vendor list
│       ├── po_matcher.py            # matches invoice to purchase order
│       ├── policy_validator.py      # checks against company payment policy rules
│       ├── fraud_checker.py         # flags duplicate invoices, changed bank details
│       ├── payment_summary.py       # builds the preview shown to user
│       └── executor.py              # ⭐ only runs after explicit approval
│
├── voice/
│   ├── stt_client.py
│   ├── tts_client.py
│   └── voice_session.py
│
├── integrations/
│   ├── gmail_client.py
│   ├── calendar_client.py
│   ├── meet_client.py
│   ├── elevenlabs_client.py
│   ├── qdrant_client.py
│   ├── openai_client.py
│   ├── ocr_provider.py              # ⭐ OCR engine (invoice scanning)
│   ├── payment_providers/
│   │   ├── stripe_client.py
│   │   ├── razorpay_client.py
│   │   └── bank_api_client.py
│   └── search_providers/
│       ├── tavily_client.py
│       ├── firecrawl_client.py
│       └── serper_client.py
│
├── models/
│   ├── user.py
│   ├── email_metadata.py
│   ├── thread.py
│   ├── draft.py
│   ├── meeting.py
│   ├── knowledge_document.py
│   ├── playbook.py
│   ├── vip_contact.py
│   ├── conversation_context.py
│   ├── agent_log.py
│   ├── vendor.py                    # ⭐ known vendors + bank detail history
│   ├── purchase_order.py            # ⭐
│   ├── payment_policy.py            # ⭐ policy rules (thresholds, approvers)
│   └── payment_record.py            # ⭐ invoice, amount, status, audit_ref
│
├── schemas/
│   ├── command_schema.py
│   ├── agent_response_schema.py
│   ├── email_schema.py
│   ├── draft_schema.py
│   ├── meeting_schema.py
│   ├── knowledge_schema.py
│   └── payment_schema.py            # ⭐ invoice/preview/approval request-response
│
├── services/
│   ├── ingestion/
│   │   ├── parser.py
│   │   └── chunker.py
│   ├── rag/
│   │   └── embedder.py
│   ├── approval/
│   │   └── approval_gate.py         # enforces approval for send/schedule/PAY
│   ├── audit/
│   │   └── audit_logger.py
│   └── payments/
│       ├── policy_engine.py         # ⭐ evaluates rules (amount limits, dual approval)
│       └── fraud_rules.py           # ⭐ duplicate/bank-change detection logic
│
├── workers/
│   ├── celery_app.py
│   ├── email_processor.py
│   ├── kb_indexer.py
│   ├── research_cache_refresh.py
│   └── invoice_scanner.py           # ⭐ background job scanning inbox for invoices
│
├── db/
│   ├── session.py
│   ├── base.py
│   └── migrations/
│
└── tests/
    ├── test_supervisor.py
    ├── test_command_center.py
    ├── test_reply_agent.py
    ├── test_calendar_agent.py
    ├── test_approval_gate.py
    ├── test_payment_agent.py        # ⭐ fraud/policy/approval test cases
    └── ...

