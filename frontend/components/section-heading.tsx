import type { ReactNode } from "react";
import { Eyebrow } from "@/components/ui/eyebrow";
import { SplitWords } from "@/components/ui/split-words";
import { cn } from "@/lib/cn";

const TITLE = "font-display text-headline font-extrabold uppercase";

type SectionHeadingProps = {
  eyebrow: string;
  title: string;
  /** Rendered on the right on wide screens, e.g. an "All projects" link. */
  action?: ReactNode;
  /** `h1` on a page whose heading this is, `h2` for a section of a page. */
  as?: "h1" | "h2";
  className?: string;
};

export function SectionHeading({ eyebrow, title, action, as: Heading = "h2", className }: SectionHeadingProps) {
  return (
    <div className={cn("flex flex-col gap-6 md:flex-row md:items-end md:justify-between", className)}>
      <div className="flex flex-col gap-4">
        <Eyebrow>{eyebrow}</Eyebrow>
        {Heading === "h1" ? (
          // A page title is on screen at load, so it never animates: no need to split it.
          <Heading className={TITLE}>{title}</Heading>
        ) : (
          // The words slide up into view as the section arrives (lib/motion).
          <Heading aria-label={title} data-motion="words" className={TITLE}>
            <SplitWords text={title} />
          </Heading>
        )}
      </div>
      {action}
    </div>
  );
}
