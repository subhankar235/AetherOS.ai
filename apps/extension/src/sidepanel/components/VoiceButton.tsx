import { useRef } from 'react';
import { useStore } from '../../lib/stores';
import { sendVoiceCommand } from '../../lib/api-client';
import { Mic, MicOff } from 'lucide-react';

export function VoiceButton() {
  const { isListening, setListening, sessionId, addTranscriptEntry } = useStore();
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const handleMouseDown = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 48000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      streamRef.current = stream;

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';

      const recorder = new MediaRecorder(stream, { mimeType });
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      recorder.start(250);
      mediaRecorderRef.current = recorder;
      setListening(true);
    } catch (err) {
      console.error('Failed to start recording:', err);
    }
  };

  const handleMouseUp = async () => {
    const recorder = mediaRecorderRef.current;
    if (!recorder) return;

    setListening(false);
    mediaRecorderRef.current = null;

    const blob = await new Promise<Blob>((resolve) => {
      recorder.onstop = () => {
        const b = new Blob(chunksRef.current, { type: recorder.mimeType });
        chunksRef.current = [];
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((t) => t.stop());
          streamRef.current = null;
        }
        resolve(b);
      };
      recorder.stop();
    });

    try {
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
        content: data.response.result?.message as string || 'Voice command processed.',
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
        if (mediaRecorderRef.current) handleMouseUp();
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
