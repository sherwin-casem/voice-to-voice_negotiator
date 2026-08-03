import { cn } from "@/lib/format";

export function Card({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <section className={cn("rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm", className)}>
      {children}
    </section>
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
    <h2 id={id} className={cn("text-base font-semibold text-zinc-900", className)}>
      {children}
    </h2>
  );
}

export function CardDescription({ children }: { children: React.ReactNode }) {
  return <p className="mt-1 text-sm text-zinc-600">{children}</p>;
}
