import { useRef } from 'react';
import { useStore } from '../../lib/stores';
import { AudioRecorder } from '../../utils/audio';
import { sendVoiceCommand } from '../../lib/api-client';
import { Mic, MicOff } from 'lucide-react';

export function VoiceButton() {
  const { isListening, setListening, sessionId, addTranscriptEntry } = useStore();
  const recorderRef = useRef<AudioRecorder | null>(null);

  const handleMouseDown = async () => {
    try {
      const recorder = new AudioRecorder();
      await recorder.startRecording();
      recorderRef.current = recorder;
      setListening(true);
    } catch (err) {
      console.error('Failed to start recording:', err);
    }
  };

  const handleMouseUp = async () => {
    const recorder = recorderRef.current;
    if (!recorder) return;

    setListening(false);
    recorderRef.current = null;

    try {
      const blob = await recorder.stopRecording();
      const data = await sendVoiceCommand(blob, sessionId);

      addTranscriptEntry({
        id: crypto.randomUUID(),
        role: 'user',
        content: `🎤 ${data.transcript}`,
        timestamp: new Date().toISOString(),
      });

      addTranscriptEntry({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: (data.response.result?.message as string) || 'Voice command processed.',
        agent_used: data.response.agent,
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      console.error('Voice command failed:', err);
    }
  };

  return (
    <div className="relative flex items-center justify-center">
      {isListening && (
        <span className="absolute inset-0 rounded-lg animate-pulse-ring" />
      )}
      <button
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={() => {
          if (recorderRef.current) handleMouseUp();
        }}
        className={`relative z-10 flex h-7 w-7 items-center justify-center rounded-lg transition-all ${
          isListening
            ? 'bg-gradient-to-br from-destructive to-destructive/80 text-destructive-foreground shadow-md shadow-destructive/30 scale-110'
            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
        }`}
        title={isListening ? 'Release to send' : 'Hold to record voice'}
      >
        {isListening ? <MicOff className="h-3.5 w-3.5" /> : <Mic className="h-3.5 w-3.5" />}
      </button>
    </div>
  );
}
