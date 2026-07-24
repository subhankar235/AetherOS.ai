import { useState } from 'react';
import { signInWithClerk } from '../../lib/auth';
import { useStore } from '../../lib/stores';
import { Sparkles } from 'lucide-react';

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
    <div className="flex h-screen flex-col items-center justify-center gap-4 p-6 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
        <Sparkles className="h-8 w-8" />
      </div>
      <h1 className="text-xl font-semibold">Aether</h1>
      <p className="text-sm text-muted-foreground">
        AI Chief of Staff for your inbox
      </p>
      <button
        onClick={handleSignIn}
        disabled={loading}
        className="mt-2 rounded-lg bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
      >
        {loading ? 'Signing in...' : 'Sign in with Clerk'}
      </button>
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  );
}
