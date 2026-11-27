import type { CSSProperties, ReactNode } from "react";
import { Markdown } from "@/components/markdown";

export type TimelineEntry = {
  id: number;
  period: string;
  title: string;
  /** Company, school or issuer, with extras such as the location. */
  subtitle: string;
  description?: string | null;
  /** Labels next to the period, e.g. "Current" or "Expired". */
  badge?: ReactNode;
  link?: { href: string; label: string };
  /** More controls beside the link, e.g. a button that opens the certificate. */
  actions?: ReactNode;
};

/** A vertical list of dated entries (jobs, schools, certificates), the dates set large. */
export function Timeline({ entries }: { entries: readonly TimelineEntry[] }) {
  return (
    <ol className="flex flex-col border-b border-line">
      {entries.map((entry, index) => (
        <li
          key={entry.id}
          data-reveal
          style={{ "--reveal": index } as CSSProperties}
          className="grid gap-4 border-t border-line py-10 md:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] md:gap-12"
        >
          <div className="flex flex-col items-start gap-3">
            <p className="font-display text-[clamp(1.75rem,3vw,2.75rem)] leading-none tracking-[-0.02em] text-muted">
              {entry.period}
            </p>
            {entry.badge}
          </div>
          <div className="flex flex-col gap-2">
            <h3 className="font-display text-[clamp(1.75rem,2.6vw,2.5rem)] leading-[0.95] tracking-[-0.02em]">{entry.title}</h3>
            <p className="text-muted">{entry.subtitle}</p>
            {entry.description && (
              <Markdown minHeading={4} className="mt-2 max-w-prose">
                {entry.description}
              </Markdown>
            )}
            {(entry.link || entry.actions) && (
              <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-3">
                {entry.actions}
                {entry.link && (
                  <a
                    href={entry.link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-fit text-sm font-semibold text-accent underline underline-offset-4"
                  >
                    {entry.link.label}
                  </a>
                )}
              </div>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}
