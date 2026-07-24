import { useState } from 'react';
import type { ActiveDraft } from '../../lib/types';
import { prepareSendDraft, executeSendDraft } from '../../lib/api-client';
import { useStore } from '../../lib/stores';
import { Sparkles, AlertTriangle } from 'lucide-react';

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
          <span className="text-xs">✕</span>
        </button>
      </div>
    </div>
  );
}
