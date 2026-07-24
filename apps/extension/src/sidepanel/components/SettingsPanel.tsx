import { useState, useEffect } from 'react';
import { useStore } from '../../lib/stores';
import {
  getGoogleIntegrationStatus,
  connectGoogle,
  disconnectGoogle,
  getUserProfile,
  updateUserPreferences,
  getUserPreferences,
} from '../../lib/api-client';
import type { GoogleIntegrationStatus, UserPreferences } from '../../lib/types';
import { Settings, X } from 'lucide-react';

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
    } catch (err) {
      console.error('Failed to load settings:', err);
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
    } catch (err) {
      console.error('Google connect failed:', err);
    }
  };

  const handleDisconnectGoogle = async () => {
    try {
      await disconnectGoogle();
      setGoogleStatus({ connected: false, scopes: [] });
    } catch (err) {
      console.error('Disconnect failed:', err);
    }
  };

  const handleSavePreferences = async () => {
    setSaving(true);
    try {
      await updateUserPreferences(prefs);
    } catch (err) {
      console.error('Save failed:', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-background">
      <header className="flex items-center justify-between border-b border-border px-3 py-2">
        <div className="flex items-center gap-2">
          <Settings className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-semibold">Settings</span>
        </div>
        <button
          onClick={onClose}
          className="rounded p-1 hover:bg-muted text-muted-foreground hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      </header>

      <div className="flex-1 overflow-y-auto space-y-4 p-4 text-sm">
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
            Google Integration
          </h2>
          <div className="rounded-lg border border-border p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs">Gmail / Calendar</span>
              <span
                className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
                  googleStatus?.connected
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : 'bg-muted text-muted-foreground'
                }`}
              >
                {googleStatus?.connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            {googleStatus?.connected ? (
              <button
                onClick={handleDisconnectGoogle}
                className="w-full rounded bg-destructive/20 px-3 py-1.5 text-xs font-medium text-destructive hover:bg-destructive/30"
              >
                Disconnect
              </button>
            ) : (
              <button
                onClick={handleConnectGoogle}
                className="w-full rounded bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90"
              >
                Connect Google
              </button>
            )}
          </div>
        </section>

        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
            Preferences
          </h2>
          <div className="rounded-lg border border-border p-3 space-y-3">
            <div className="space-y-1">
              <label className="text-[10px] font-medium text-muted-foreground">Timezone</label>
              <input
                type="text"
                value={prefs.timezone || ''}
                onChange={(e) => setPrefs({ ...prefs, timezone: e.target.value })}
                placeholder="e.g. America/New_York"
                className="w-full rounded border border-input bg-background px-2 py-1.5 text-xs outline-none focus:border-primary"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] font-medium text-muted-foreground">Language</label>
              <input
                type="text"
                value={prefs.language || ''}
                onChange={(e) => setPrefs({ ...prefs, language: e.target.value })}
                placeholder="e.g. en"
                className="w-full rounded border border-input bg-background px-2 py-1.5 text-xs outline-none focus:border-primary"
              />
            </div>
            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                checked={prefs.voice_history_opt_in || false}
                onChange={(e) =>
                  setPrefs({ ...prefs, voice_history_opt_in: e.target.checked })
                }
                className="rounded border-input"
              />
              Opt in to voice history
            </label>
            <button
              onClick={handleSavePreferences}
              disabled={saving}
              className="w-full rounded bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Preferences'}
            </button>
          </div>
        </section>

        <section>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
            Account
          </h2>
          <div className="rounded-lg border border-border p-3 space-y-1">
            <div className="text-xs">
              <span className="text-muted-foreground">User ID:</span>{' '}
              <span className="font-mono text-[10px]">{authUserId}</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
