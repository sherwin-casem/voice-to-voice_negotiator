import { API_ROUTES } from "@voice/shared";

import { getWebSocketUrl } from "./api-client";
import type { ServerWsEnvelope } from "@/types/websocket";

export type WsEventHandler = (envelope: ServerWsEnvelope) => void;

export class InterviewWebSocket {
  private socket: WebSocket | null = null;

  constructor(
    private readonly sessionId: string,
    private readonly userId: string,
  ) {}

  connect(onMessage: WsEventHandler, onStateChange?: (open: boolean) => void): void {
    const path = API_ROUTES.voiceWebSocket(this.sessionId, this.userId);
    this.socket = new WebSocket(getWebSocketUrl(path));

    this.socket.onopen = () => onStateChange?.(true);
    this.socket.onclose = () => onStateChange?.(false);
    this.socket.onerror = () => onStateChange?.(false);
    this.socket.onmessage = (event) => {
      try {
        const envelope = JSON.parse(event.data as string) as ServerWsEnvelope;
        onMessage(envelope);
      } catch {
        onMessage({
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

  send(type: string, payload: Record<string, unknown>, requestId?: string): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return;
    }
    this.socket.send(
      JSON.stringify({
        type,
        payload,
        request_id: requestId,
      }),
    );
  }

  disconnect(): void {
    this.socket?.close();
    this.socket = null;
  }
}
