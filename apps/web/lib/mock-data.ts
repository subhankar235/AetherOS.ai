export type Priority = "high" | "medium" | "low";
export type Category = "investor" | "customer" | "team" | "newsletter" | "billing" | "personal";

export interface Email {
  id: string;
  from: string;
  fromEmail: string;
  subject: string;
  preview: string;
  body: string;
  summary: string;
  category: Category;
  priority: Priority;
  urgent: boolean;
  unread: boolean;
  receivedAt: string;
  labels: string[];
}

export const emails: Email[] = [
  {
    id: "e1",
    from: "Sarah Chen",
    fromEmail: "sarah@sequoiacap.com",
    subject: "Follow-up on Series A term sheet",
    preview: "Great chatting yesterday. Attaching the redline...",
    body: "Hi,\n\nGreat chatting yesterday. Attaching the redline on the term sheet — a couple of points around board composition and the option pool we'd like to discuss. Can we hop on a call Thursday afternoon?\n\nBest,\nSarah",
    summary: "Sequoia sent redlined term sheet, wants a Thursday PM call to discuss board seats and option pool.",
    category: "investor",
    priority: "high",
    urgent: true,
    unread: true,
    receivedAt: "2026-07-15T09:12:00Z",
    labels: ["Series A", "Legal"],
  },
  {
    id: "e2",
    from: "Marcus Feld",
    fromEmail: "marcus@acme.io",
    subject: "Renewal contract — need signature by Friday",
    preview: "Attaching the renewal for another 12 months...",
    body: "Hey team,\n\nAttaching the renewal for another 12 months at the same terms. Legal reviewed on our side. Would love to close this out by Friday if possible.\n\nThanks,\nMarcus",
    summary: "Acme's 12-month renewal is ready to sign; Marcus wants it closed by Friday.",
    category: "customer",
    priority: "high",
    urgent: true,
    unread: true,
    receivedAt: "2026-07-15T08:41:00Z",
    labels: ["Renewal"],
  },
  {
    id: "e3",
    from: "Priya Ramesh",
    fromEmail: "priya@team.internal",
    subject: "Design review deck for Monday",
    preview: "Sharing the v3 deck for the onboarding revamp...",
    body: "Hi,\n\nSharing v3 of the onboarding revamp deck. Would love your comments before Monday's review so we can incorporate.\n\nCheers,\nPriya",
    summary: "Priya shared v3 of the onboarding deck; needs feedback before Monday's design review.",
    category: "team",
    priority: "medium",
    urgent: false,
    unread: true,
    receivedAt: "2026-07-15T07:20:00Z",
    labels: ["Design"],
  },
  {
    id: "e4",
    from: "Stripe",
    fromEmail: "receipts@stripe.com",
    subject: "Invoice #INV-2088 — $4,320.00 due",
    preview: "Your monthly Stripe invoice is ready...",
    body: "Your monthly invoice for July is available. Amount due: $4,320.00. Auto-charge will occur on July 20.",
    summary: "Stripe July invoice $4,320 auto-charges July 20.",
    category: "billing",
    priority: "medium",
    urgent: false,
    unread: false,
    receivedAt: "2026-07-14T22:05:00Z",
    labels: ["Invoice"],
  },
  {
    id: "e5",
    from: "The Information",
    fromEmail: "newsletter@theinformation.com",
    subject: "Weekly briefing: AI infra shakeup",
    preview: "The 5 stories that mattered this week...",
    body: "Top stories this week: OpenAI's new inference chip, Anthropic funding round, and more.",
    summary: "Weekly tech newsletter — AI infra roundup.",
    category: "newsletter",
    priority: "low",
    urgent: false,
    unread: false,
    receivedAt: "2026-07-14T14:00:00Z",
    labels: [],
  },
  {
    id: "e6",
    from: "Jordan Alvarez",
    fromEmail: "jordan@bigco.com",
    subject: "Question about SSO / SAML setup",
    preview: "We're rolling this out to 400 seats and need SAML...",
    body: "Hi support,\n\nWe're rolling out to 400 seats next week and need SAML SSO via Okta. What's the setup path?\n\nJordan",
    summary: "Enterprise customer BigCo needs Okta SAML SSO setup for 400 seats next week.",
    category: "customer",
    priority: "high",
    urgent: false,
    unread: true,
    receivedAt: "2026-07-15T06:11:00Z",
    labels: ["Support", "Enterprise"],
  },
  {
    id: "e7",
    from: "Mom",
    fromEmail: "mom@family.com",
    subject: "Sunday dinner?",
    preview: "Are you free this Sunday? Making lasagna...",
    body: "Hi honey, are you free Sunday? Making lasagna.",
    summary: "Mom asking if you're free Sunday for lasagna.",
    category: "personal",
    priority: "low",
    urgent: false,
    unread: false,
    receivedAt: "2026-07-13T18:30:00Z",
    labels: [],
  },
];

export interface Draft {
  id: string;
  emailId: string;
  to: string;
  subject: string;
  body: string;
  tone: "casual" | "warm" | "formal" | "concise";
  status: "pending_approval" | "approved" | "sent";
  createdAt: string;
}

export const drafts: Draft[] = [
  {
    id: "d1",
    emailId: "e1",
    to: "sarah@sequoiacap.com",
    subject: "Re: Follow-up on Series A term sheet",
    body: "Hi Sarah,\n\nThanks for the redline. Thursday afternoon works — how about 3pm PT? I'll have our counsel on the line so we can move through the board and option pool points efficiently.\n\nTalk soon,",
    tone: "warm",
    status: "pending_approval",
    createdAt: "2026-07-15T09:20:00Z",
  },
  {
    id: "d2",
    emailId: "e6",
    to: "jordan@bigco.com",
    subject: "Re: Question about SSO / SAML setup",
    body: "Hi Jordan,\n\nHappy to help — SAML via Okta is a 20-minute config on our end. I'll send over our IdP metadata and a short setup doc today, and we can do a working session before your rollout.\n\nBest,",
    tone: "concise",
    status: "pending_approval",
    createdAt: "2026-07-15T06:45:00Z",
  },
];

export interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  attendees: string[];
  status: "pending_approval" | "confirmed";
  source: string;
}

export const events: CalendarEvent[] = [
  {
    id: "c1",
    title: "Sequoia term sheet review",
    start: "2026-07-16T15:00:00Z",
    end: "2026-07-16T16:00:00Z",
    attendees: ["sarah@sequoiacap.com", "you@company.com"],
    status: "pending_approval",
    source: "Drafted from email e1",
  },
  {
    id: "c2",
    title: "Design review — onboarding v3",
    start: "2026-07-20T17:00:00Z",
    end: "2026-07-20T18:00:00Z",
    attendees: ["priya@team.internal", "you@company.com"],
    status: "confirmed",
    source: "Recurring team meeting",
  },
  {
    id: "c3",
    title: "BigCo Okta setup working session",
    start: "2026-07-17T20:00:00Z",
    end: "2026-07-17T20:30:00Z",
    attendees: ["jordan@bigco.com"],
    status: "pending_approval",
    source: "Drafted from email e6",
  },
];

export interface Payment {
  id: string;
  vendor: string;
  amount: number;
  currency: string;
  invoiceRef: string;
  dueDate: string;
  status: "pending_approval" | "approved" | "paid" | "flagged";
  policyChecks: { label: string; passed: boolean }[];
  fraudScore: number;
}

export const payments: Payment[] = [
  {
    id: "p1",
    vendor: "AWS",
    amount: 12480.55,
    currency: "USD",
    invoiceRef: "AWS-2026-07",
    dueDate: "2026-07-25",
    status: "pending_approval",
    policyChecks: [
      { label: "Vendor on approved list", passed: true },
      { label: "Amount within monthly cap", passed: true },
      { label: "Duplicate invoice check", passed: true },
    ],
    fraudScore: 4,
  },
  {
    id: "p2",
    vendor: "Unknown Contractor LLC",
    amount: 8900,
    currency: "USD",
    invoiceRef: "INV-99213",
    dueDate: "2026-07-18",
    status: "flagged",
    policyChecks: [
      { label: "Vendor on approved list", passed: false },
      { label: "Bank account matches records", passed: false },
      { label: "Duplicate invoice check", passed: true },
    ],
    fraudScore: 78,
  },
  {
    id: "p3",
    vendor: "Notion",
    amount: 240,
    currency: "USD",
    invoiceRef: "NTN-08812",
    dueDate: "2026-07-22",
    status: "paid",
    policyChecks: [
      { label: "Vendor on approved list", passed: true },
      { label: "Amount within monthly cap", passed: true },
    ],
    fraudScore: 2,
  },
];

export interface KnowledgeDoc {
  id: string;
  title: string;
  source: string;
  updatedAt: string;
  chunks: number;
  tags: string[];
}

export const knowledgeDocs: KnowledgeDoc[] = [
  { id: "k1", title: "Company voice & tone guide", source: "Notion", updatedAt: "2026-07-10", chunks: 42, tags: ["writing", "policy"] },
  { id: "k2", title: "Sales playbook 2026", source: "Google Drive", updatedAt: "2026-07-01", chunks: 128, tags: ["sales"] },
  { id: "k3", title: "Legal — MSA templates", source: "Upload", updatedAt: "2026-06-20", chunks: 56, tags: ["legal"] },
  { id: "k4", title: "Support macros & FAQ", source: "Zendesk", updatedAt: "2026-07-12", chunks: 210, tags: ["support"] },
  { id: "k5", title: "Product one-pager", source: "Upload", updatedAt: "2026-05-18", chunks: 8, tags: ["product"] },
];

export interface ResearchReport {
  id: string;
  company: string;
  requestedAt: string;
  status: "completed" | "running";
  highlights: string[];
}

export const reports: ResearchReport[] = [
  {
    id: "r1",
    company: "Sequoia Capital",
    requestedAt: "2026-07-14",
    status: "completed",
    highlights: [
      "Recently led rounds in 4 AI infra companies",
      "Sarah Chen is on 6 boards, typically leads Series A",
      "Term sheets tend to include 20% option pool refresh",
    ],
  },
  {
    id: "r2",
    company: "BigCo Inc.",
    requestedAt: "2026-07-15",
    status: "running",
    highlights: [],
  },
];

export interface Ticket {
  id: string;
  customer: string;
  subject: string;
  status: "open" | "waiting" | "resolved";
  priority: Priority;
  updatedAt: string;
}

export const tickets: Ticket[] = [
  { id: "t1", customer: "BigCo (Jordan)", subject: "SAML SSO setup", status: "open", priority: "high", updatedAt: "2026-07-15" },
  { id: "t2", customer: "Acme (Marcus)", subject: "Contract renewal signature", status: "waiting", priority: "high", updatedAt: "2026-07-15" },
  { id: "t3", customer: "Beacon Labs", subject: "Data export bug", status: "open", priority: "medium", updatedAt: "2026-07-14" },
  { id: "t4", customer: "Halide Studio", subject: "How to invite teammates", status: "resolved", priority: "low", updatedAt: "2026-07-13" },
];

export interface AuditEntry {
  id: string;
  actor: string;
  action: string;
  target: string;
  agent: string;
  approvedBy: string;
  at: string;
}

export const auditLog: AuditEntry[] = [
  { id: "a1", actor: "Reply Agent", action: "sent_email", target: "sarah@sequoiacap.com", agent: "reply", approvedBy: "user", at: "2026-07-15T09:32:00Z" },
  { id: "a2", actor: "Calendar Agent", action: "created_event", target: "Sequoia term sheet review", agent: "calendar", approvedBy: "user", at: "2026-07-15T09:33:00Z" },
  { id: "a3", actor: "Payment Agent", action: "flagged_payment", target: "Unknown Contractor LLC — $8,900", agent: "payment", approvedBy: "system", at: "2026-07-15T08:14:00Z" },
  { id: "a4", actor: "Inbox Agent", action: "categorized", target: "e2 → customer/high", agent: "inbox", approvedBy: "system", at: "2026-07-15T08:41:05Z" },
  { id: "a5", actor: "Knowledge Agent", action: "answered_query", target: "\"What's our refund policy?\"", agent: "knowledge", approvedBy: "user", at: "2026-07-14T21:11:00Z" },
];

export interface Approval {
  id: string;
  kind: "reply" | "calendar" | "payment";
  summary: string;
  detail: string;
  requestedAt: string;
  agent: string;
}

export const approvals: Approval[] = [
  { id: "ap1", kind: "reply", summary: "Send reply to Sarah Chen (Sequoia)", detail: "Warm-toned reply confirming Thursday 3pm PT call.", requestedAt: "2026-07-15T09:20:00Z", agent: "Reply Agent" },
  { id: "ap2", kind: "calendar", summary: "Create event: Sequoia term sheet review", detail: "Thu Jul 16, 3:00–4:00pm PT with sarah@sequoiacap.com", requestedAt: "2026-07-15T09:21:00Z", agent: "Calendar Agent" },
  { id: "ap3", kind: "payment", summary: "Pay AWS invoice $12,480.55", detail: "All 3 policy checks passed, fraud score 4/100.", requestedAt: "2026-07-15T08:00:00Z", agent: "Payment Agent" },
  { id: "ap4", kind: "payment", summary: "REVIEW: Unknown Contractor LLC — $8,900", detail: "Vendor not on approved list. Bank details mismatch. Fraud score 78/100.", requestedAt: "2026-07-15T08:14:00Z", agent: "Payment Agent" },
];

export interface CommandTranscript {
  id: string;
  role: "user" | "assistant";
  mode: "voice" | "text";
  content: string;
  agentUsed?: string;
  at: string;
}

export const initialTranscript: CommandTranscript[] = [
  { id: "m1", role: "user", mode: "voice", content: "What came in from investors this week?", at: "2026-07-15T09:10:00Z" },
  { id: "m2", role: "assistant", mode: "voice", content: "You've got 3 investor emails this week — Sequoia is the important one. They sent back a redline on the term sheet and want a call Thursday. Want me to draft a reply?", agentUsed: "Inbox Agent", at: "2026-07-15T09:10:04Z" },
  { id: "m3", role: "user", mode: "voice", content: "Yeah, draft it and keep it warm.", at: "2026-07-15T09:10:20Z" },
  { id: "m4", role: "assistant", mode: "voice", content: "Draft is ready — confirming Thursday 3pm PT with counsel on the line. Ready to send when you approve.", agentUsed: "Reply Agent", at: "2026-07-15T09:10:28Z" },
];