import { getStoredToken } from './auth';
import type { WsEvent } from './types';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

type EventHandler = (event: WsEvent) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<EventHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private shouldReconnect = false;

  async connect(): Promise<void> {
    const token = await getStoredToken();
    if (!token) {
      console.warn('[WS] No token available, cannot connect');
      return;
    }

    this.shouldReconnect = true;
    this.reconnectAttempts = 0;
    this._connect(token);
  }

  private _connect(token: string): void {
    if (this.ws) {
      this.ws.close();
    }

    const url = `${WS_URL}?token=${encodeURIComponent(token)}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('[WS] Connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WsEvent;
        this._emit(data.type, data);
      } catch (err) {
        console.warn('[WS] Failed to parse message:', err);
      }
    };

    this.ws.onclose = (event) => {
      console.log(`[WS] Disconnected (code: ${event.code})`);
      this.ws = null;
      if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
        this.reconnectAttempts++;
        console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
        setTimeout(() => {
          getStoredToken().then((token) => {
            if (token) this._connect(token);
          });
        }, delay);
      }
    };

    this.ws.onerror = (error) => {
      console.error('[WS] Error:', error);
    };
  }

  disconnect(): void {
    this.shouldReconnect = false;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  sendPing(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send('ping');
    }
  }

  on(eventType: string, handler: EventHandler): void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(handler);
  }

  off(eventType: string, handler: EventHandler): void {
    this.listeners.get(eventType)?.delete(handler);
  }

  private _emit(eventType: string, event: WsEvent): void {
    const handlers = this.listeners.get(eventType);
    if (handlers) {
      handlers.forEach((handler) => handler(event));
    }
    const wildcardHandlers = this.listeners.get('*');
    if (wildcardHandlers) {
      wildcardHandlers.forEach((handler) => handler(event));
    }
  }

  get connected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

export const wsClient = new WebSocketClient();
