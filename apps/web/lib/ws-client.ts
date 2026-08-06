import { API_ROUTES } from "@voice/shared";

import { getWebSocketUrl } from "./api-client";
import type { ServerWsEnvelope } from "@/types/websocket";

export type WsEventHandler = (envelope: ServerWsEnvelope) => void;

export interface InterviewWebSocketOptions {
  maxReconnectAttempts?: number;
  reconnectBaseDelayMs?: number;
}

export class InterviewWebSocket {
  private socket: WebSocket | null = null;
  private intentionalClose = false;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private onMessage: WsEventHandler | null = null;
  private onConnectionChange: ((connected: boolean, reconnecting: boolean) => void) | null = null;

  constructor(
    private readonly sessionId: string,
    private readonly accessToken: string,
    private readonly options: InterviewWebSocketOptions = {},
  ) {}

  connect(
    onMessage: WsEventHandler,
    onConnectionChange?: (connected: boolean, reconnecting: boolean) => void,
  ): void {
    this.onMessage = onMessage;
    this.onConnectionChange = onConnectionChange ?? null;
    this.intentionalClose = false;
    this.reconnectAttempts = 0;
    this.openSocket(false);
  }

  send(type: string, payload: Record<string, unknown>, requestId?: string): boolean {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return false;
    }
    this.socket.send(
      JSON.stringify({
        type,
        payload,
        request_id: requestId,
      }),
    );
    return true;
  }

  disconnect(): void {
    this.intentionalClose = true;
    this.clearReconnectTimer();
    this.socket?.close();
    this.socket = null;
    this.onConnectionChange?.(false, false);
  }

  get isOpen(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  private openSocket(isReconnect: boolean): void {
    if (this.intentionalClose) {
      return;
    }

    this.onConnectionChange?.(false, isReconnect);

    const path = API_ROUTES.voiceWebSocket(this.sessionId, this.accessToken);
    this.socket = new WebSocket(getWebSocketUrl(path));

    this.socket.onopen = () => {
      this.reconnectAttempts = 0;
      this.onConnectionChange?.(true, false);
    };

    this.socket.onclose = () => {
      this.socket = null;
      if (this.intentionalClose) {
        this.onConnectionChange?.(false, false);
        return;
      }
      this.scheduleReconnect();
    };

    this.socket.onerror = () => {
      if (this.intentionalClose) {
        return;
      }
      this.onMessage?.({
        type: "session.error",
        payload: {
          code: "CONNECTION_ERROR",
          message: "WebSocket connection failed",
          recoverable: true,
        },
      });
    };

    this.socket.onmessage = (event) => {
      try {
        const envelope = JSON.parse(event.data as string) as ServerWsEnvelope;
        this.onMessage?.(envelope);
      } catch {
        this.onMessage?.({
          type: "session.error",
          payload: {
            code: "INVALID_MESSAGE",
            message: "Received malformed WebSocket message",
            recoverable: true,
          },
        });
      }
    };
  }

  private scheduleReconnect(): void {
    const maxAttempts = this.options.maxReconnectAttempts ?? 3;
    if (this.reconnectAttempts >= maxAttempts) {
      this.onConnectionChange?.(false, false);
      this.onMessage?.({
        type: "session.error",
        payload: {
          code: "RECONNECT_FAILED",
          message: "Unable to reconnect to the voice session.",
          recoverable: false,
        },
      });
      return;
    }

    this.reconnectAttempts += 1;
    const baseDelay = this.options.reconnectBaseDelayMs ?? 1000;
    const delay = baseDelay * this.reconnectAttempts;
    this.onConnectionChange?.(false, true);

    this.clearReconnectTimer();
    this.reconnectTimer = setTimeout(() => {
      this.openSocket(true);
    }, delay);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}
