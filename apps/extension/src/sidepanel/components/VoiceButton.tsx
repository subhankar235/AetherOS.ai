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
    <button
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={() => {
        if (recorderRef.current) handleMouseUp();
      }}
      className={`rounded-lg p-2 transition-colors ${
        isListening
          ? 'bg-destructive text-destructive-foreground animate-pulse'
          : 'bg-muted text-muted-foreground hover:bg-muted/80'
      }`}
      title={isListening ? 'Release to send' : 'Hold to record voice'}
    >
      {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
    </button>
  );
}
