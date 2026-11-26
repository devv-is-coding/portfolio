import type { ReactNode } from "react";
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

/** A vertical list of dated entries: jobs, schools, certificates. */
export function Timeline({ entries }: { entries: readonly TimelineEntry[] }) {
  return (
    <ol className="flex flex-col">
      {entries.map((entry) => (
        <li key={entry.id} className="grid gap-3 border-t border-line py-8 md:grid-cols-[14rem_1fr] md:gap-10">
          <p className="flex flex-wrap items-center gap-3 font-mono text-xs uppercase tracking-[0.2em] text-muted">
            {entry.period}
            {entry.badge}
          </p>
          <div className="flex flex-col gap-2">
            <h3 className="font-display text-2xl font-extrabold">{entry.title}</h3>
            <p className="text-muted">{entry.subtitle}</p>
            {entry.description && (
              <Markdown minHeading={4} className="mt-2 max-w-prose">
                {entry.description}
              </Markdown>
            )}
            {(entry.link || entry.actions) && (
              <div className="mt-2 flex flex-wrap items-center gap-x-6 gap-y-3">
                {entry.actions}
                {entry.link && (
                  <a
                    href={entry.link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-fit text-sm text-accent underline underline-offset-4"
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
