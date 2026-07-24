import { useState } from 'react';
import type { ActiveCalendarProposal } from '../../lib/types';
import { confirmCalendarEvent } from '../../lib/api-client';
import { useStore } from '../../lib/stores';
import { CalendarIcon, Video, Check, X } from 'lucide-react';

interface CalendarCardProps {
  proposal: ActiveCalendarProposal;
}

export function CalendarCard({ proposal }: CalendarCardProps) {
  const [confirming, setConfirming] = useState(false);
  const setActiveProposal = useStore((s) => s.setActiveProposal);

  const handleConfirm = async () => {
    setConfirming(true);
    try {
      await confirmCalendarEvent(proposal.approval_id || proposal.preview_id, proposal.preview_id);
      setActiveProposal(null);
    } catch (err: unknown) {
      alert(`Failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setConfirming(false);
    }
  };

  return (
    <div className="group relative overflow-hidden rounded-xl border border-emerald-500/25 bg-gradient-to-b from-card to-emerald-500/[0.02] shadow-sm transition-all hover:border-emerald-500/35 hover:shadow-md">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-500/30 to-transparent" />

      <div className="p-3 space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <div className="flex h-5 w-5 items-center justify-center rounded-md bg-emerald-500/10">
              <CalendarIcon className="h-3 w-3 text-emerald-400" />
            </div>
            <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">
              Calendar Proposal
            </span>
          </div>
          <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[9px] font-semibold text-emerald-400 border border-emerald-500/20">
            Awaiting Approval
          </span>
        </div>

        <div className="space-y-1.5 text-xs">
          <div className="flex items-start gap-1.5">
            <span className="mt-0.5 shrink-0 text-muted-foreground">Title:</span>
            <span className="font-semibold text-foreground/90 leading-snug">{proposal.title}</span>
          </div>
          <div className="flex items-start gap-1.5">
            <span className="mt-0.5 shrink-0 text-muted-foreground">Time:</span>
            <span className="font-medium text-foreground/80 leading-snug">
              {new Date(proposal.start).toLocaleString([], {
                dateStyle: 'medium',
                timeStyle: 'short',
              })}{' '}
              –{' '}
              {new Date(proposal.end).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>
          {proposal.attendees.length > 0 && (
            <div className="flex items-start gap-1.5">
              <span className="mt-0.5 shrink-0 text-muted-foreground">With:</span>
              <span className="font-medium text-foreground/80 leading-snug">
                {proposal.attendees.join(', ')}
              </span>
            </div>
          )}
          {proposal.meet_link && (
            <div className="flex items-center gap-1.5 text-emerald-400 bg-emerald-500/5 rounded-lg px-2 py-1.5">
              <Video className="h-3 w-3 shrink-0" />
              <span className="text-[10px] truncate font-medium">{proposal.meet_link}</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 pt-0.5">
          <button
            onClick={handleConfirm}
            disabled={confirming}
            className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-emerald-500 px-3 py-2 text-xs font-bold text-white shadow-sm transition-all hover:from-emerald-500 hover:to-emerald-400 hover:shadow-md active:scale-[0.98] disabled:opacity-40 disabled:hover:shadow-none disabled:active:scale-100"
          >
            {confirming ? (
              <>
                <div className="h-3 w-3 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Check className="h-3 w-3" />
                Approve & Create
              </>
            )}
          </button>
          <button
            onClick={() => setActiveProposal(null)}
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
