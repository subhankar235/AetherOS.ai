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
      <div className="flex h-screen items-center justify-center text-sm text-muted-foreground">
        Loading...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AuthGate />;
  }

  return (
    <div className="flex h-screen flex-col bg-background text-foreground">
      <Header wsConnected={wsConnected} />

      <div className="flex-1 overflow-y-auto space-y-3 p-3">
        {activeDraft && <DraftCard draft={activeDraft} />}
        {activeProposal && <CalendarCard proposal={activeProposal} />}
        <Transcript />
      </div>

      <CommandBar />

      {showSettings && <SettingsPanel onClose={() => setShowSettings(false)} />}
    </div>
  );
}
