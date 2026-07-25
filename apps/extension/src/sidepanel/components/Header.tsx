import { useStore } from '../../lib/stores';
import { Sparkles, Settings, LogOut } from 'lucide-react';

interface HeaderProps {
  onSettingsClick: () => void;
}

export function Header({ onSettingsClick }: HeaderProps) {
  const { authEmail, logout, wsConnected } = useStore();

  return (
    <header className="flex items-center justify-between border-b border-border bg-card/50 px-3 py-2.5">
      <div className="flex items-center gap-2.5">
        <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-accent">
          <Sparkles className="h-3.5 w-3.5 text-white" />
        </div>
        <span className="text-sm font-bold tracking-tight">Aether</span>
        <div className="flex items-center gap-1 rounded-md bg-muted px-1.5 py-0.5">
          <span className={`h-1.5 w-1.5 rounded-full ${wsConnected ? 'bg-emerald-500' : 'bg-muted-foreground'}`} />
          <span className="text-[9px] font-medium text-muted-foreground uppercase">
            {wsConnected ? 'Live' : 'Offline'}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-0.5">
        <span className="hidden text-[11px] text-muted-foreground truncate max-w-[100px] mr-1">
          {authEmail}
        </span>
        <button
          onClick={onSettingsClick}
          className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          title="Settings"
        >
          <Settings className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={logout}
          className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-destructive"
          title="Sign out"
        >
          <LogOut className="h-3.5 w-3.5" />
        </button>
      </div>
    </header>
  );
}
