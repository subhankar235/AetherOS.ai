import { useEffect, useRef } from 'react';
import { useStore } from '../../lib/stores';
import type { TranscriptEntry } from '../../lib/types';

export function Transcript() {
  const transcript = useStore((s) => s.transcript);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript]);

  if (transcript.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center text-xs text-muted-foreground">
        <p>Type a command below to get started.</p>
        <p className="mt-1">e.g., "show me my unread emails"</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {transcript.map((entry) => (
        <TranscriptBubble key={entry.id} entry={entry} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}

function TranscriptBubble({ entry }: { entry: TranscriptEntry }) {
  const isUser = entry.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
          isUser
            ? 'bg-secondary text-secondary-foreground'
            : 'border border-primary/30 bg-primary/5'
        }`}
      >
        {!isUser && (
          <div className="mb-1 flex items-center gap-1.5">
            <span className="text-[10px] font-medium text-muted-foreground uppercase">
              Aether
            </span>
            {entry.agent_used && (
              <span className="rounded border border-border px-1 py-0 text-[9px] text-muted-foreground">
                {entry.agent_used}
              </span>
            )}
          </div>
        )}
        <p className="whitespace-pre-wrap leading-relaxed">{entry.content}</p>
      </div>
    </div>
  );
}
