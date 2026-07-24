import { useStore } from '../../lib/stores';
import { Sparkles, Wifi, WifiOff, LogOut } from 'lucide-react';

interface HeaderProps {
  wsConnected: boolean;
}

export function Header({ wsConnected }: HeaderProps) {
  const { authEmail, logout } = useStore();

  return (
    <header className="flex items-center justify-between border-b border-border px-3 py-2">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-primary" />
        <span className="text-sm font-semibold">Aether</span>
        {wsConnected ? (
          <Wifi className="h-3 w-3 text-emerald-500" />
        ) : (
          <WifiOff className="h-3 w-3 text-muted-foreground" />
        )}
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground truncate max-w-[120px]">
          {authEmail}
        </span>
        <button
          onClick={logout}
          className="rounded p-1 hover:bg-muted text-muted-foreground hover:text-foreground"
          title="Sign out"
        >
          <LogOut className="h-3.5 w-3.5" />
        </button>
      </div>
    </header>
  );
}
