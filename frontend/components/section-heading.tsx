import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

type SectionHeadingProps = {
  title: string;
  /** Rendered on the right on wide screens, e.g. a "See all" link. */
  action?: ReactNode;
  className?: string;
};

/**
 * A section's title inside a page (the about page's Experience, Education...): the bold narrow
 * headline, no label above it. A page's own title is a `PosterHeading as="h1"`.
 */
export function SectionHeading({ title, action, className }: SectionHeadingProps) {
  return (
    <div className={cn("flex flex-col gap-6 md:flex-row md:items-end md:justify-between", className)}>
      <h2 className="font-display text-headline">{title}</h2>
      {action}
    </div>
  );
}
