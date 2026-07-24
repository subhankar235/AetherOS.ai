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

export async function sendTextCommand(
  command: string,
  sessionId: string
): Promise<CommandResponse> {
  const headers = await getFormHeaders();
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

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/dashboard/summary`, { headers });
  if (!res.ok) throw new Error(`Dashboard summary failed: ${res.status}`);
  return res.json();
}

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

export async function listPlaybooks(): Promise<Playbook[]> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/playbooks`, { headers });
  if (!res.ok) throw new Error(`List playbooks failed: ${res.status}`);
  return res.json();
}

export async function listVipContacts(): Promise<VIPContact[]> {
  const headers = await getHeaders();
  const res = await fetch(`${API_URL}/vip-contacts`, { headers });
  if (!res.ok) throw new Error(`List VIP contacts failed: ${res.status}`);
  return res.json();
}
