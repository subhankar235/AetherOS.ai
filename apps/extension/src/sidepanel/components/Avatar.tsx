import { useStore } from '../../lib/stores';
import { Sparkles } from 'lucide-react';

export function Avatar() {
  const { isListening, isSpeaking } = useStore();

  const stateClass = isSpeaking
    ? 'animate-pulse shadow-[0_0_30px_var(--color-primary)]'
    : isListening
    ? 'animate-pulse'
    : '';

  const label = isSpeaking
    ? 'Speaking...'
    : isListening
    ? 'Listening...'
    : 'Idle';

  return (
    <div className="flex flex-col items-center gap-2 py-4">
      <div
        className={`relative h-20 w-20 rounded-full bg-gradient-to-br from-primary via-primary/70 to-accent transition-all ${stateClass}`}
      >
        <div className="absolute inset-0 flex items-center justify-center">
          <Sparkles className="h-6 w-6 text-primary-foreground" />
        </div>
      </div>
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
    </div>
  );
}
