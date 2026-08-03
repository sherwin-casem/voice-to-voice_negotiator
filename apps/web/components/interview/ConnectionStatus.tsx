import type { WsConnectionState } from "@/types/websocket";

import { Badge } from "@/components/ui/Badge";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { cn } from "@/lib/format";

const STATE_LABELS: Record<WsConnectionState, string> = {
  idle: "Not connected",
  connecting: "Connecting",
  connected: "Connected",
  disconnected: "Disconnected",
  error: "Connection error",
};

const STATE_STYLES: Record<WsConnectionState, string> = {
  idle: "bg-zinc-100 text-zinc-700",
  connecting: "bg-amber-50 text-amber-700",
  connected: "bg-emerald-50 text-emerald-700",
  disconnected: "bg-zinc-100 text-zinc-700",
  error: "bg-red-50 text-red-700",
};

export function ConnectionStatus({ state }: { state: WsConnectionState }) {
  return (
    <Card aria-labelledby="connection-status-title">
      <CardTitle id="connection-status-title">Connection</CardTitle>
      <CardDescription>Real-time voice pipeline status.</CardDescription>
      <div className="mt-4">
        <Badge className={cn(STATE_STYLES[state])} aria-live="polite">
          {STATE_LABELS[state]}
        </Badge>
      </div>
    </Card>
  );
}
