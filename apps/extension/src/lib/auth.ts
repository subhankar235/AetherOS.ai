import type { AuthState } from './types';

const CLERK_SIGN_IN_URL = `https://${import.meta.env.VITE_CLERK_FRONTEND_API}/sign-in`;

const STORAGE_KEY_TOKEN = 'clerk_session_token';
const STORAGE_KEY_USER = 'clerk_user_info';

export async function getStoredToken(): Promise<string | null> {
  const result = await chrome.storage.local.get(STORAGE_KEY_TOKEN);
  return result[STORAGE_KEY_TOKEN] || null;
}

export async function getStoredUserInfo(): Promise<{ userId: string; email: string } | null> {
  const result = await chrome.storage.local.get(STORAGE_KEY_USER);
  return result[STORAGE_KEY_USER] || null;
}

export async function setStoredAuth(token: string, userId: string, email: string): Promise<void> {
  await chrome.storage.local.set({
    [STORAGE_KEY_TOKEN]: token,
    [STORAGE_KEY_USER]: { userId, email },
  });
}

export async function clearStoredAuth(): Promise<void> {
  await chrome.storage.local.remove([STORAGE_KEY_TOKEN, STORAGE_KEY_USER]);
}

export function onAuthChanged(callback: (token: string | null) => void): () => void {
  const listener = (changes: Record<string, chrome.storage.StorageChange>) => {
    if (changes[STORAGE_KEY_TOKEN]) {
      callback(changes[STORAGE_KEY_TOKEN].newValue || null);
    }
  };
  chrome.storage.onChanged.addListener(listener);
  return () => chrome.storage.onChanged.removeListener(listener);
}

export async function signInWithClerk(): Promise<AuthState> {
  return new Promise((resolve, reject) => {
    chrome.identity.launchWebAuthFlow(
      {
        url: CLERK_SIGN_IN_URL,
        interactive: true,
      },
      async (responseUrl) => {
        if (chrome.runtime.lastError || !responseUrl) {
          reject(new Error(chrome.runtime.lastError?.message || 'Sign in cancelled'));
          return;
        }

        const url = new URL(responseUrl);
        const sessionToken = url.hash
          ? new URLSearchParams(url.hash.slice(1)).get('clerk_session_jwt')
          : url.searchParams.get('clerk_session_jwt');

        if (!sessionToken) {
          reject(new Error('No session token in callback'));
          return;
        }

        const payload = JSON.parse(atob(sessionToken.split('.')[1]));
        const userId = payload.sub;
        const email = payload.email || payload.email_address || '';

        await setStoredAuth(sessionToken, userId, email);

        resolve({
          token: sessionToken,
          userId,
          email,
          isLoaded: true,
        });
      }
    );
  });
}

export async function signOut(): Promise<void> {
  await clearStoredAuth();
}

export async function getHeaders(): Promise<Record<string, string>> {
  const token = await getStoredToken();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export async function getFormHeaders(): Promise<Record<string, string>> {
  const token = await getStoredToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}
