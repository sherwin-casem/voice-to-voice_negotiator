import { GlassPanel } from "@/components/ui/GlassPanel";

export function SessionNotesPanel({ notes }: { notes: string[] }) {
  return (
    <GlassPanel className="flex h-full max-h-full min-h-0 flex-col overflow-hidden p-4 sm:p-5">
      <h2 className="text-section-label mb-3 shrink-0">Session brief</h2>
      <ul className="min-h-0 space-y-2.5 overflow-y-auto">
        {notes.map((note) => {
          const [label, ...rest] = note.split(": ");
          const value = rest.length > 0 ? rest.join(": ") : null;
          return (
            <li
              key={note}
              className="rounded-xl border border-white/5 bg-white/[0.03] px-3 py-2.5"
            >
              {value ? (
                <>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">
                    {label}
                  </p>
                  <p className="mt-1 text-sm font-medium text-[var(--text-primary)]">{value}</p>
                </>
              ) : (
                <p className="text-sm text-[var(--text-muted)]">{note}</p>
              )}
            </li>
          );
        })}
      </ul>
      <div className="mt-4 shrink-0 border-t border-white/5 pt-3 lg:mt-auto">
        <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">
          Quick tips
        </p>
        <ul className="mt-2 space-y-1.5 text-xs leading-relaxed text-slate-400">
          <li>Use headphones to cut echo.</li>
          <li>Pause briefly before answering.</li>
          <li>Finish answer when you are done speaking.</li>
        </ul>
      </div>
    </GlassPanel>
  );
}
