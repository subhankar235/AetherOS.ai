import { useState, useEffect } from 'react';
import { useStore } from '../../lib/stores';
import {
  getGoogleIntegrationStatus,
  connectGoogle,
  disconnectGoogle,
  updateUserPreferences,
  getUserPreferences,
} from '../../lib/api-client';
import type { GoogleIntegrationStatus, UserPreferences } from '../../lib/types';
import { Settings, X, Globe, User, ChevronRight } from 'lucide-react';

interface SettingsPanelProps {
  onClose: () => void;
}

export function SettingsPanel({ onClose }: SettingsPanelProps) {
  const [googleStatus, setGoogleStatus] = useState<GoogleIntegrationStatus | null>(null);
  const [prefs, setPrefs] = useState<UserPreferences>({});
  const [saving, setSaving] = useState(false);
  const authUserId = useStore((s) => s.authUserId);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const [status, preferences] = await Promise.all([
        getGoogleIntegrationStatus(),
        getUserPreferences(),
      ]);
      setGoogleStatus(status);
      setPrefs(preferences);
    } catch {
      // Settings load silently
    }
  };

  const handleConnectGoogle = async () => {
    try {
      const url = await connectGoogle();
      const popup = window.open(url, 'google-oauth', 'width=600,height=700');
      const poll = setInterval(async () => {
        if (popup?.closed) {
          clearInterval(poll);
          const status = await getGoogleIntegrationStatus();
          setGoogleStatus(status);
        }
      }, 500);
    } catch {
      // Connect failed silently
    }
  };

  const handleDisconnectGoogle = async () => {
    try {
      await disconnectGoogle();
      setGoogleStatus({ connected: false, scopes: [] });
    } catch {
      // Disconnect failed silently
    }
  };

  const handleSavePreferences = async () => {
    setSaving(true);
    try {
      await updateUserPreferences(prefs);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-background animate-slide-up">
      <header className="flex items-center justify-between border-b border-border bg-card/50 px-4 py-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-muted">
            <Settings className="h-3.5 w-3.5 text-muted-foreground" />
          </div>
          <span className="text-sm font-bold">Settings</span>
        </div>
        <button
          onClick={onClose}
          className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      </header>

      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        <section>
          <div className="mb-2.5 flex items-center gap-2">
            <Globe className="h-3.5 w-3.5 text-muted-foreground" />
            <h2 className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
              Google Integration
            </h2>
          </div>
          <div className="rounded-xl border border-border bg-card p-3.5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <span className="text-sm font-medium text-foreground/90">Gmail & Calendar</span>
                <p className="text-[11px] text-muted-foreground">
                  {googleStatus?.connected
                    ? 'Your Google account is connected'
                    : 'Connect to manage email and events'}
                </p>
              </div>
              <span
                className={`shrink-0 text-[10px] font-semibold px-2.5 py-1 rounded-full ${
                  googleStatus?.connected
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : 'bg-muted text-muted-foreground border border-border'
                }`}
              >
                {googleStatus?.connected ? 'Connected' : 'Off'}
              </span>
            </div>
            {googleStatus?.connected ? (
              <button
                onClick={handleDisconnectGoogle}
                className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-destructive/20 bg-destructive/5 px-3 py-2 text-xs font-semibold text-destructive transition-colors hover:bg-destructive/10"
              >
                Disconnect Google
              </button>
            ) : (
              <button
                onClick={handleConnectGoogle}
                className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-bold text-primary-foreground shadow-sm transition-all hover:bg-primary/90 active:scale-[0.98]"
              >
                <ChevronRight className="h-3 w-3" />
                Connect Google
              </button>
            )}
          </div>
        </section>

        <section>
          <div className="mb-2.5 flex items-center gap-2">
            <User className="h-3.5 w-3.5 text-muted-foreground" />
            <h2 className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
              Preferences
            </h2>
          </div>
          <div className="rounded-xl border border-border bg-card p-3.5 space-y-3.5">
            <div className="space-y-1.5">
              <label className="text-[11px] font-medium text-muted-foreground">Timezone</label>
              <input
                type="text"
                value={prefs.timezone || ''}
                onChange={(e) => setPrefs({ ...prefs, timezone: e.target.value })}
                placeholder="e.g. America/New_York"
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground placeholder-muted-foreground/50 outline-none transition-colors focus:border-primary/60 focus:shadow-[0_0_8px_rgba(99,102,241,0.1)]"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-[11px] font-medium text-muted-foreground">Language</label>
              <input
                type="text"
                value={prefs.language || ''}
                onChange={(e) => setPrefs({ ...prefs, language: e.target.value })}
                placeholder="e.g. en"
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground placeholder-muted-foreground/50 outline-none transition-colors focus:border-primary/60 focus:shadow-[0_0_8px_rgba(99,102,241,0.1)]"
              />
            </div>
            <label className="flex cursor-pointer items-center gap-3 rounded-lg bg-muted/30 px-3 py-2.5 transition-colors hover:bg-muted/50">
              <input
                type="checkbox"
                checked={prefs.voice_history_opt_in || false}
                onChange={(e) =>
                  setPrefs({ ...prefs, voice_history_opt_in: e.target.checked })
                }
                className="h-4 w-4 rounded border-input accent-primary"
              />
              <div className="space-y-0.5">
                <span className="text-sm font-medium text-foreground/90">Voice History</span>
                <p className="text-[10px] text-muted-foreground">
                  Save voice recordings to improve accuracy
                </p>
              </div>
            </label>
            <button
              onClick={handleSavePreferences}
              disabled={saving}
              className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-bold text-primary-foreground shadow-sm transition-all hover:bg-primary/90 active:scale-[0.98] disabled:opacity-40 disabled:active:scale-100"
            >
              {saving ? (
                <>
                  <div className="h-3 w-3 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                  Saving...
                </>
              ) : (
                'Save Preferences'
              )}
            </button>
          </div>
        </section>

        <section>
          <div className="mb-2.5 flex items-center gap-2">
            <User className="h-3.5 w-3.5 text-muted-foreground" />
            <h2 className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
              Account
            </h2>
          </div>
          <div className="rounded-xl border border-border bg-card p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">User ID</span>
              <span className="text-[10px] font-mono text-foreground/60">{authUserId}</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
