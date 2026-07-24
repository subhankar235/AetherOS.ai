import { useState } from 'react';
import { signInWithClerk } from '../../lib/auth';
import { useStore } from '../../lib/stores';
import { Sparkles, LogIn } from 'lucide-react';

export function AuthGate() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const setAuthenticated = useStore((s) => s.setAuthenticated);

  const handleSignIn = async () => {
    setLoading(true);
    setError(null);
    try {
      const authState = await signInWithClerk();
      setAuthenticated(authState.token!, authState.userId!, authState.email!);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Sign in failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex h-screen flex-col items-center justify-center overflow-hidden bg-background px-6">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--primary)_0%,_transparent_60%)] opacity-15" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_bottom,_var(--accent)_0%,_transparent_60%)] opacity-10" />

      <div className="relative flex flex-col items-center gap-5 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary via-primary/80 to-accent shadow-lg shadow-primary/20">
          <Sparkles className="h-8 w-8 text-white" />
        </div>

        <div className="space-y-1.5">
          <h1 className="text-2xl font-bold tracking-tight">Aether</h1>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-[260px]">
            AI Chief of Staff for your inbox
          </p>
        </div>

        <button
          onClick={handleSignIn}
          disabled={loading}
          className="mt-2 flex items-center gap-2 rounded-xl bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:bg-primary/90 hover:shadow-primary/30 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:hover:scale-100"
        >
          {loading ? (
            <>
              <div className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
              Signing in...
            </>
          ) : (
            <>
              <LogIn className="h-4 w-4" />
              Sign in with Clerk
            </>
          )}
        </button>

        {error && (
          <p className="animate-fade-in text-sm text-destructive bg-destructive/10 px-3 py-1.5 rounded-lg">
            {error}
          </p>
        )}
      </div>
    </div>
  );
}
