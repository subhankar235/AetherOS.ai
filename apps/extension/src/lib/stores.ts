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
  isAuthenticated: boolean;
  authEmail: string | null;
  authUserId: string | null;
  isAuthLoading: boolean;

  sessionId: string;
  transcript: TranscriptEntry[];
  isCommandLoading: boolean;

  activeDraft: ActiveDraft | null;
  activeProposal: ActiveCalendarProposal | null;
  queryResults: EmailMetadata[];

  isListening: boolean;
  isSpeaking: boolean;

  wsConnected: boolean;

  unreadCount: number;

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

function getSessionId(): string {
  const key = 'aether_session_id';
  const stored = localStorage.getItem(key);
  if (stored) return stored;
  const id = crypto.randomUUID();
  localStorage.setItem(key, id);
  return id;
}

export const useStore = create<ExtensionState>((set, get) => ({
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
      const r = respObj.result as Record<string, unknown>;
      const c = respObj.context_updates as Record<string, unknown>;

      let responseText = 'Task completed successfully.';
      if (r?.message) responseText = r.message as string;
      else if (respObj.status === 'clarification_needed') {
        responseText = (r?.clarification as string) || 'Could you please clarify?';
      } else if (r?.summary) responseText = r.summary as string;
      else if (r?.answer) responseText = r.answer as string;
      else if (typeof r === 'string') responseText = r;

      const items: EmailMetadata[] =
        (r?.items as EmailMetadata[]) || (c?.last_search_results as EmailMetadata[]) || [];
      if (items.length > 0) {
        set({ queryResults: items });
      }

      const draftId =
        (r?.draft_id as string) || (c?.active_draft_id as string);
      const draftBody =
        (r?.draft_body as string) || (c?.active_draft_body as string);
      if (draftId && draftBody) {
        set({
          activeDraft: {
            draft_id: draftId,
            draft_body: draftBody,
            has_gaps:
              (r?.has_gaps as boolean) ??
              (c?.has_gaps as boolean) ??
              false,
            gap_notes:
              (r?.gap_notes as string[]) ??
              (c?.gap_notes as string[]) ??
              [],
            recipient:
              ((r?.target_email as Record<string, string>)?.sender) || items[0]?.sender || 'Recipient',
            subject:
              ((r?.target_email as Record<string, string>)?.subject) || items[0]?.subject || 'Reply Draft',
          },
        });
      }

      const previewId =
        (r?.preview_id as string) ||
        (c?.active_calendar_preview_id as string);
      const approvalId =
        (r?.approval_id as string) ||
        (c?.active_calendar_approval_id as string);
      if (previewId && r?.start && r?.end) {
        set({
          activeProposal: {
            preview_id: previewId,
            approval_id: approvalId,
            title: (r?.title as string) || 'Meeting Proposal',
            start: r.start as string,
            end: r.end as string,
            duration_minutes: (r?.duration_minutes as number) || 60,
            attendees: (r?.participants as string[]) || [],
            meet_link: r?.meet_link as string,
            double_booking_warnings: r?.double_booking_warnings as unknown[],
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
