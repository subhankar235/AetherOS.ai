import { getStoredToken } from '../lib/auth';

let currentToken: string | null = null;

async function initAuth() {
  currentToken = await getStoredToken();
}

initAuth();

chrome.storage.onChanged.addListener((changes) => {
  if (changes.clerk_session_token) {
    currentToken = changes.clerk_session_token.newValue || null;
    if (currentToken) {
      updateBadge();
    } else {
      chrome.action.setBadgeText({ text: '' });
    }
  }
});

chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create('poll-dashboard', { periodInMinutes: 5 });
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'poll-dashboard' && currentToken) {
    updateBadge();
  }
});

async function updateBadge() {
  if (!currentToken) return;

  try {
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const res = await fetch(`${API_URL}/dashboard/summary`, {
      headers: { Authorization: `Bearer ${currentToken}` },
    });

    if (res.ok) {
      const data = await res.json();
      const count = (data.high_priority || 0) + (data.pending_approvals || 0);

      chrome.action.setBadgeText({
        text: count > 0 ? String(count) : '',
      });
      chrome.action.setBadgeBackgroundColor({
        color: count > 0 ? '#ef4444' : '#22c55e',
      });
    }
  } catch (err) {
    console.warn('[Badge] Poll failed:', err);
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'AUTH_UPDATED') {
    currentToken = message.token;
    sendResponse({ success: true });
  }
  if (message.type === 'GET_TOKEN') {
    sendResponse({ token: currentToken });
  }
  if (message.type === 'OPEN_SIDE_PANEL' && sender.tab?.id) {
    chrome.sidePanel.open({ tabId: sender.tab.id });
    sendResponse({ success: true });
  }
  return true;
});

chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch(console.error);
