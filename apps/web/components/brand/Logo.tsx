import Image from "next/image";
import Link from "next/link";

import { cn } from "@/lib/format";

type LogoProps = {
  className?: string;
  href?: string;
  showTagline?: boolean;
  size?: "sm" | "md";
};

export function Logo({
  className,
  href = "/",
  showTagline = true,
  size = "md",
}: LogoProps) {
  const iconSize = size === "sm" ? 32 : 40;
  const wordmarkClass =
    size === "sm" ? "text-base font-semibold" : "text-lg font-semibold";

  const content = (
    <div className={cn("flex items-center gap-3", className)}>
      <Image
        src="/logo-icon.svg"
        alt=""
        width={iconSize}
        height={iconSize}
        aria-hidden
        priority
      />
      <div className="min-w-0">
        <p className={cn(wordmarkClass, "leading-tight text-[var(--text-primary)]")}>
          Vox<span className="text-teal-400">Forge</span>
        </p>
        {showTagline ? (
          <p className="text-xs font-medium uppercase tracking-widest text-teal-400/80">
            AI Voice Interview Practice
          </p>
        ) : null}
      </div>
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="rounded-lg outline-offset-4 hover:opacity-90">
        {content}
      </Link>
    );
  }

  return content;
}
