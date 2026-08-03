import { cn } from "@/lib/format";

export function GlassPanel({
  className,
  children,
  strong = false,
}: {
  className?: string;
  children: React.ReactNode;
  strong?: boolean;
}) {
  return (
    <div className={cn(strong ? "glass-panel-strong" : "glass-panel", className)}>{children}</div>
  );
}
