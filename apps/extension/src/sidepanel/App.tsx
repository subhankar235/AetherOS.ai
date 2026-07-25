import { useEffect, useState } from 'react';
import { useStore } from '../lib/stores';
import { wsClient } from '../lib/websocket-client';
import { AuthGate } from './components/AuthGate';
import { Header } from './components/Header';
import { Transcript } from './components/Transcript';
import { CommandBar } from './components/CommandBar';
import { DraftCard } from './components/DraftCard';
import { CalendarCard } from './components/CalendarCard';
import { SettingsPanel } from './components/SettingsPanel';
import { Sparkles } from 'lucide-react';

export default function App() {
  const {
    isAuthenticated,
    isAuthLoading,
    initAuth,
    wsConnected,
    setWsConnected,
    activeDraft,
    activeProposal,
  } = useStore();
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  useEffect(() => {
    if (isAuthenticated) {
      wsClient.on('connected', () => setWsConnected(true));
      wsClient.connect();

      return () => {
        wsClient.disconnect();
        setWsConnected(false);
      };
    }
  }, [isAuthenticated, setWsConnected]);

  if (isAuthLoading) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 bg-background">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
          <Sparkles className="h-6 w-6 text-primary animate-pulse-glow" />
        </div>
        <div className="h-3 w-24 rounded animate-shimmer" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AuthGate />;
  }

  return (
    <div className="flex h-screen flex-col bg-background text-foreground">
      <Header onSettingsClick={() => setShowSettings(true)} />

      <div className="flex-1 overflow-y-auto space-y-3 p-3">
        {activeDraft && (
          <div className="animate-fade-in-up">
            <DraftCard draft={activeDraft} />
          </div>
        )}
        {activeProposal && (
          <div className="animate-fade-in-up">
            <CalendarCard proposal={activeProposal} />
          </div>
        )}
        <Transcript />
      </div>

      <CommandBar />

      {showSettings && <SettingsPanel onClose={() => setShowSettings(false)} />}
    </div>
  );
}
