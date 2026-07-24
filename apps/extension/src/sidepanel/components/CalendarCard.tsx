import { useState } from 'react';
import type { ActiveCalendarProposal } from '../../lib/types';
import { confirmCalendarEvent } from '../../lib/api-client';
import { useStore } from '../../lib/stores';
import { CalendarIcon, Video } from 'lucide-react';

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
    <div className="rounded-lg border border-emerald-500/60 bg-card p-3 shadow-sm space-y-2">
      <div className="flex items-center justify-between border-b pb-1.5">
        <div className="flex items-center gap-1.5">
          <CalendarIcon className="h-3.5 w-3.5 text-emerald-500" />
          <span className="text-[10px] font-semibold text-emerald-600 uppercase tracking-wider">
            Calendar Proposal
          </span>
        </div>
        <span className="rounded border border-emerald-500/50 px-1.5 py-0 text-[9px] text-emerald-600">
          Awaiting Approval
        </span>
      </div>

      <div className="space-y-1 text-xs">
        <div>
          <span className="font-medium text-muted-foreground">Title:</span>{' '}
          <span className="font-medium">{proposal.title}</span>
        </div>
        <div>
          <span className="font-medium text-muted-foreground">Time:</span>{' '}
          <span className="font-medium">
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
          <div>
            <span className="font-medium text-muted-foreground">Attendees:</span>{' '}
            <span className="font-medium">{proposal.attendees.join(', ')}</span>
          </div>
        )}
        {proposal.meet_link && (
          <div className="flex items-center gap-1 text-emerald-600">
            <Video className="h-3 w-3" />
            <span className="text-[10px] truncate">{proposal.meet_link}</span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={handleConfirm}
          disabled={confirming}
          className="flex-1 rounded bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {confirming ? 'Creating...' : 'Approve & Create'}
        </button>
        <button
          onClick={() => setActiveProposal(null)}
          className="rounded p-1.5 text-muted-foreground hover:text-destructive"
        >
          <span className="text-xs">✕</span>
        </button>
      </div>
    </div>
  );
}
