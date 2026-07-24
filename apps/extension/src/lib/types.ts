export interface AuthState {
  token: string | null;
  userId: string | null;
  email: string | null;
  isLoaded: boolean;
}

export interface AgentResponse {
  agent: string;
  status: 'waiting_for_user' | 'completed' | 'error' | 'clarification_needed';
  result: Record<string, unknown>;
  context_updates: Record<string, unknown>;
  requires_approval: boolean;
}

export type AgentStatus = AgentResponse['status'];

export interface CommandResponse {
  session_id: string;
  response: AgentResponse;
}

export interface VoiceCommandResponse extends CommandResponse {
  transcript: string;
}

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

export interface ActiveDraft {
  draft_id: string;
  draft_body: string;
  has_gaps?: boolean;
  gap_notes?: string[];
  recipient?: string;
  subject?: string;
  created_at?: string;
}

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

export interface DashboardSummary {
  total_emails: number;
  high_priority: number;
  unread: number;
  recent_meetings: number;
  pending_approvals: number;
}

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

export interface GoogleIntegrationStatus {
  connected: boolean;
  scopes: string[];
  is_expired?: boolean;
  revoked?: boolean;
  expires_at?: string;
}

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

export interface VIPContact {
  id: string;
  user_id: string;
  contact_email: string;
  contact_name?: string | null;
  added_at: string;
}

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

export interface ApiError {
  error: {
    code: string;
    message: string;
    request_id: string;
    details?: Record<string, unknown>;
  };
}
