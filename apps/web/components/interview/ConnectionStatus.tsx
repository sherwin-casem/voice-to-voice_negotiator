import type { WsConnectionState } from "@/types/websocket";

import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/format";

const STATE_LABELS: Record<WsConnectionState, string> = {
  idle: "Not connected",
  connecting: "Connecting",
  connected: "Connected",
  reconnecting: "Reconnecting",
  disconnected: "Disconnected",
  error: "Connection error",
};

const STATE_STYLES: Record<WsConnectionState, string> = {
  idle: "bg-white/10 text-[var(--text-muted)]",
  connecting: "bg-amber-500/15 text-amber-300",
  connected: "bg-teal-500/20 text-teal-300",
  reconnecting: "bg-amber-500/15 text-amber-300",
  disconnected: "bg-white/10 text-[var(--text-muted)]",
  error: "bg-red-500/15 text-red-300",
};

export function ConnectionStatus({ state }: { state: WsConnectionState }) {
  return (
    <Badge className={cn(STATE_STYLES[state])} aria-live="polite">
      {STATE_LABELS[state]}
    </Badge>
  );
}
