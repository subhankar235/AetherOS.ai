import { useState } from 'react';
import type { ActiveDraft } from '../../lib/types';
import { prepareSendDraft, executeSendDraft } from '../../lib/api-client';
import { useStore } from '../../lib/stores';
import { Sparkles, AlertTriangle, Send, X } from 'lucide-react';

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
    <div className="group relative overflow-hidden rounded-xl border border-primary/30 bg-gradient-to-b from-card to-primary/[0.02] shadow-sm transition-all hover:border-primary/40 hover:shadow-md">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent" />

      <div className="p-3 space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <div className="flex h-5 w-5 items-center justify-center rounded-md bg-primary/10">
              <Sparkles className="h-3 w-3 text-primary" />
            </div>
            <span className="text-[10px] font-bold text-primary uppercase tracking-wider">
              AI Reply Draft
            </span>
          </div>
          <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-[9px] font-semibold text-amber-400 border border-amber-500/20">
            Awaiting Approval
          </span>
        </div>

        {draft.recipient && (
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-muted-foreground">To:</span>
            <span className="font-semibold text-foreground/90">{draft.recipient}</span>
          </div>
        )}

        {draft.has_gaps && draft.gap_notes && draft.gap_notes.length > 0 && (
          <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-2.5 space-y-1">
            <div className="flex items-center gap-1.5 text-[11px] font-semibold text-amber-400">
              <AlertTriangle className="h-3 w-3" />
              <span>Knowledge Gap</span>
            </div>
            {draft.gap_notes.map((note, i) => (
              <p key={i} className="text-[10px] text-amber-300/70 leading-relaxed">{note}</p>
            ))}
          </div>
        )}

        <div className="max-h-28 overflow-y-auto rounded-lg border border-border bg-muted/30 p-2.5 text-xs leading-relaxed text-foreground/80 whitespace-pre-wrap">
          {draft.draft_body}
        </div>

        <div className="flex items-center gap-2 pt-0.5">
          <button
            onClick={handleApproveAndSend}
            disabled={sending}
            className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-gradient-to-r from-primary to-primary/90 px-3 py-2 text-xs font-bold text-primary-foreground shadow-sm transition-all hover:from-primary/90 hover:to-primary/80 hover:shadow-md active:scale-[0.98] disabled:opacity-40 disabled:hover:shadow-none disabled:active:scale-100"
          >
            {sending ? (
              <>
                <div className="h-3 w-3 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                Sending...
              </>
            ) : (
              <>
                <Send className="h-3 w-3" />
                Approve & Send
              </>
            )}
          </button>
          <button
            onClick={() => setActiveDraft(null)}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-destructive"
            title="Discard"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
