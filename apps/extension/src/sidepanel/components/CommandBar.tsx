import { useState } from 'react';
import { useStore } from '../../lib/stores';
import { VoiceButton } from './VoiceButton';
import { Send } from 'lucide-react';

export function CommandBar() {
  const [input, setInput] = useState('');
  const { sendCommand, isCommandLoading } = useStore();

  const handleSubmit = () => {
    if (!input.trim() || isCommandLoading) return;
    sendCommand(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-border bg-card/30 px-2 py-2">
      <div className="flex items-center gap-2 rounded-xl border border-input bg-background px-2.5 py-1 transition-all focus-within:border-primary/60 focus-within:shadow-[0_0_12px_rgba(99,102,241,0.15)]">
        <VoiceButton />
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isCommandLoading}
          placeholder="Type a command..."
          className="flex-1 bg-transparent py-2 text-sm text-foreground placeholder-muted-foreground outline-none disabled:opacity-40"
        />
        <button
          onClick={handleSubmit}
          disabled={isCommandLoading || !input.trim()}
          className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary text-primary-foreground transition-all hover:bg-primary/90 hover:scale-[1.05] active:scale-95 disabled:opacity-30 disabled:hover:scale-100"
        >
          <Send className={`h-3.5 w-3.5 ${isCommandLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>
    </div>
  );
}
