import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

const BASE = "inline-flex items-center rounded-btn border px-3 py-1 text-label font-medium";

type TagProps = {
  children: ReactNode;
  /** Makes the tag a filter link. */
  href?: string;
  /** The filter that is on right now. */
  active?: boolean;
  className?: string;
};

/** A small label: a skill, a category, a filter. */
export function Tag({ children, href, active = false, className }: TagProps) {
  const style = cn(
    BASE,
    active ? "border-accent bg-accent text-accent-ink" : "border-line text-muted",
    href && !active && "transition-colors hover:border-accent hover:text-accent",
    // A tag that links is a tap target: 44 px tall on touch screens (28 px with a mouse).
    href && "pointer-coarse:min-h-11 pointer-coarse:px-4",
    className,
  );
  // A plain link, not next/link: pages show dozens of tags, and each next/link is a client
  // component that hydrates and prefetches. For filter tags a full page load is fine.
  if (href) {
    return (
      <a href={href} className={style} aria-current={active ? "page" : undefined}>
        {children}
      </a>
    );
  }
  return <span className={style}>{children}</span>;
}
