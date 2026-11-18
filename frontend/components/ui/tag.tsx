import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

const BASE = "inline-flex items-center rounded-full border px-3 py-1 font-mono text-xs uppercase tracking-wider";

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
