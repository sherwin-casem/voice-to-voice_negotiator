import { cn } from "@/lib/format";

export function Card({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <section className={cn("glass-panel p-5", className)}>{children}</section>
  );
}

export function CardTitle({
  children,
  className,
  id,
}: {
  children: React.ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <h2 id={id} className={cn("text-section-label", className)}>
      {children}
    </h2>
  );
}

export function CardDescription({ children }: { children: React.ReactNode }) {
  return <p className="mt-2 text-sm leading-relaxed text-[var(--text-muted)]">{children}</p>;
}

export function CardHeading({
  children,
  className,
  id,
}: {
  children: React.ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <h2 id={id} className={cn("text-lg font-semibold text-[var(--text-primary)]", className)}>
      {children}
    </h2>
  );
}
