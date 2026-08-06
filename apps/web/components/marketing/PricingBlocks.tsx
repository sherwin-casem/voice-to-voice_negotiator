import { Fragment } from "react";

import { AuthEntryButtonLink } from "@/components/auth/AuthEntryLink";
import { cn } from "@/lib/format";

export function PricingTierCards({
  tiers,
}: {
  tiers: ReadonlyArray<{
    id: string;
    name: string;
    price: string;
    period: string;
    description: string;
    highlights: ReadonlyArray<string>;
    cta: { label: string; href: string };
    featured: boolean;
  }>;
}) {
  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {tiers.map((tier) => (
        <article
          key={tier.id}
          className={cn(
            "glass-panel flex flex-col p-6",
            tier.featured && "border-teal-500/30 ring-1 ring-teal-500/20",
          )}
        >
          {tier.featured ? (
            <p className="mb-3 inline-flex w-fit rounded-full bg-teal-500/15 px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-teal-300">
              Most popular
            </p>
          ) : null}
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">{tier.name}</h3>
          <p className="mt-3">
            <span className="text-3xl font-semibold text-[var(--text-primary)]">{tier.price}</span>
            <span className="ml-2 text-sm text-[var(--text-muted)]">{tier.period}</span>
          </p>
          <p className="mt-3 text-sm text-[var(--text-muted)]">{tier.description}</p>
          <ul className="mt-6 flex-1 space-y-2 text-sm text-[var(--text-muted)]">
            {tier.highlights.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="text-teal-500" aria-hidden="true">
                  ✓
                </span>
                {item}
              </li>
            ))}
          </ul>
          <AuthEntryButtonLink
            href={tier.cta.href}
            variant={tier.featured ? "primary" : "secondary"}
            className="mt-6 w-full justify-center py-2"
          >
            {tier.cta.label}
          </AuthEntryButtonLink>
        </article>
      ))}
    </div>
  );
}

type ComparisonValue = boolean | string;

function ComparisonCell({ value }: { value: ComparisonValue }) {
  if (value === true) {
    return <span className="text-teal-400">✓</span>;
  }
  if (value === false) {
    return <span className="text-[var(--text-dim)]">—</span>;
  }
  return <span className="text-sm text-[var(--text-muted)]">{value}</span>;
}

export function PricingComparisonTable({
  categories,
}: {
  categories: ReadonlyArray<{
    name: string;
    features: ReadonlyArray<{
      label: string;
      free: ComparisonValue;
      pro: ComparisonValue;
      team: ComparisonValue;
    }>;
  }>;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-[var(--border-glass)]">
            <th scope="col" className="py-3 pr-4 font-medium text-[var(--text-muted)]">
              Feature
            </th>
            <th scope="col" className="px-4 py-3 font-medium text-[var(--text-primary)]">
              Free
            </th>
            <th scope="col" className="px-4 py-3 font-medium text-teal-300">
              Pro
            </th>
            <th scope="col" className="px-4 py-3 font-medium text-[var(--text-primary)]">
              Team
            </th>
          </tr>
        </thead>
        <tbody>
          {categories.map((category) => (
            <Fragment key={category.name}>
              <tr className="border-b border-[var(--border-glass)]">
                <th
                  scope="colgroup"
                  colSpan={4}
                  className="py-4 text-left text-xs font-semibold uppercase tracking-widest text-[var(--text-dim)]"
                >
                  {category.name}
                </th>
              </tr>
              {category.features.map((feature) => (
                <tr key={feature.label} className="border-b border-[var(--border-glass)]/60">
                  <th scope="row" className="py-3 pr-4 font-normal text-[var(--text-primary)]">
                    {feature.label}
                  </th>
                  <td className="px-4 py-3">
                    <ComparisonCell value={feature.free} />
                  </td>
                  <td className="px-4 py-3">
                    <ComparisonCell value={feature.pro} />
                  </td>
                  <td className="px-4 py-3">
                    <ComparisonCell value={feature.team} />
                  </td>
                </tr>
              ))}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function FaqAccordion({
  items,
}: {
  items: ReadonlyArray<{ question: string; answer: string }>;
}) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details
          key={item.question}
          className="glass-panel group open:bg-[var(--bg-panel-hover)] [&_summary::-webkit-details-marker]:hidden"
        >
          <summary className="cursor-pointer list-none px-5 py-4 font-medium text-[var(--text-primary)] marker:content-none">
            {item.question}
          </summary>
          <div className="border-t border-[var(--border-glass)] px-5 py-4 text-sm leading-relaxed text-[var(--text-muted)]">
            {item.answer}
          </div>
        </details>
      ))}
    </div>
  );
}
