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
    <div className="border-t border-border p-2">
      <div className="flex items-center gap-2">
        <VoiceButton />
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isCommandLoading}
          placeholder="Type a command..."
          className="flex-1 rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary disabled:opacity-50"
        />
        <button
          onClick={handleSubmit}
          disabled={isCommandLoading || !input.trim()}
          className="rounded-lg bg-primary p-2 text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          <Send className={`h-4 w-4 ${isCommandLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>
    </div>
  );
}
