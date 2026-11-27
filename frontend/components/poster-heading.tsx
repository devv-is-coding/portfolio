import type { ReactNode } from "react";

type PosterHeadingProps = {
  title: string;
  /** How many items the section shows, set small in the accent after the title. */
  count?: number;
  /** On the right on wide screens, under the title on phones: e.g. a "See all" link. */
  action?: ReactNode;
  /** `h1` when it is the page's own heading (e.g. /contact), `h2` for a section. */
  as?: "h1" | "h2";
};

/** A section's poster headline: the title set huge, an optional count, an optional link. */
export function PosterHeading({ title, count, action, as: Heading = "h2" }: PosterHeadingProps) {
  return (
    <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
      <Heading className="font-display text-poster">
        {title}
        {count !== undefined && (
          <sup className="ml-[0.08em] align-super text-[0.24em] tracking-normal text-accent">({count})</sup>
        )}
      </Heading>
      {action && <div className="md:pb-3">{action}</div>}
    </div>
  );
}
