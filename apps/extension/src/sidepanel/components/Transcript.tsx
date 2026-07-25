import { useEffect, useRef } from 'react';
import { useStore } from '../../lib/stores';
import type { TranscriptEntry } from '../../lib/types';
import { MessageSquare, Sparkles } from 'lucide-react';

export function Transcript() {
  const transcript = useStore((s) => s.transcript);
  const isCommandLoading = useStore((s) => s.isCommandLoading);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript, isCommandLoading]);

  if (transcript.length === 0 && !isCommandLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted/50 mb-4">
          <MessageSquare className="h-5 w-5 text-muted-foreground/60" />
        </div>
        <p className="text-sm font-medium text-muted-foreground">
          Type a command to get started
        </p>
        <p className="mt-1 text-xs text-muted-foreground/60">
          e.g. &quot;show my unread emails&quot;
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {transcript.map((entry, i) => (
        <div key={entry.id} className="animate-fade-in" style={{ animationDelay: `${i * 30}ms` }}>
          <TranscriptBubble entry={entry} />
        </div>
      ))}
      {isCommandLoading && (
        <div className="flex justify-start animate-fade-in">
          <div className="flex items-center gap-2 rounded-xl border border-primary/20 bg-primary/5 px-3.5 py-2.5">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            <div className="flex items-center gap-1">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}

function TranscriptBubble({ entry }: { entry: TranscriptEntry }) {
  const isUser = entry.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[88%] rounded-xl px-3.5 py-2.5 text-sm leading-relaxed ${
          isUser
            ? 'bg-primary text-primary-foreground shadow-sm shadow-primary/20'
            : 'border border-border bg-card'
        }`}
      >
        {!isUser && (
          <div className="mb-1.5 flex items-center gap-1.5">
            <Sparkles className="h-3 w-3 text-primary" />
            <span className="text-[10px] font-semibold text-primary tracking-wide uppercase">
              Aether
            </span>
            {entry.agent_used && (
              <span className="rounded-md bg-muted px-1.5 py-0.5 text-[9px] font-medium text-muted-foreground">
                {entry.agent_used}
              </span>
            )}
          </div>
        )}
        <p className="whitespace-pre-wrap break-words">{entry.content}</p>
      </div>
    </div>
  );
}
