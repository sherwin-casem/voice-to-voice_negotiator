import { cn } from "@/lib/format";

const fieldClass =
  "w-full rounded-xl border border-[var(--border-glass)] bg-white/5 px-3 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-dim)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-500";

const selectClass =
  "cursor-pointer appearance-none pr-10 transition-colors hover:border-[var(--border-glass-strong)] hover:bg-white/[0.07] disabled:cursor-not-allowed disabled:opacity-50 aria-[invalid=true]:border-red-500/60 aria-[invalid=true]:focus-visible:outline-red-500";

function SelectChevron() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <path
        d="M5 7.5L10 12.5L15 7.5"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={cn(fieldClass, props.className)} />;
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className="relative">
      <select {...props} className={cn(fieldClass, selectClass, props.className)} />
      <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-teal-400/80">
        <SelectChevron />
      </span>
    </div>
  );
}

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={cn(fieldClass, "min-h-[120px]", props.className)} />;
}

export function Label({
  htmlFor,
  children,
  required,
}: {
  htmlFor?: string;
  children: React.ReactNode;
  required?: boolean;
}) {
  return (
    <label htmlFor={htmlFor} className="mb-1.5 block text-sm font-medium text-[var(--text-primary)]">
      {children}
      {required ? <span className="text-red-400"> *</span> : null}
    </label>
  );
}

export function FieldError({ message }: { message?: string | null }) {
  if (!message) {
    return null;
  }
  return (
    <p role="alert" className="mt-1 text-sm text-red-400">
      {message}
    </p>
  );
}

export function FieldHint({ children }: { children: React.ReactNode }) {
  return <p className="mt-1 text-xs text-[var(--text-dim)]">{children}</p>;
}
