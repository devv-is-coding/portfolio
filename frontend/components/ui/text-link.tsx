import Link from "next/link";
import type { ReactNode } from "react";

const STYLE =
  "group inline-flex items-center gap-2 border-b-2 border-accent pb-1 font-semibold transition-colors hover:text-accent pointer-coarse:min-h-11";

type TextLinkProps = {
  href: string;
  children: ReactNode;
  /** A file or another site (e.g. the résumé PDF): opens in a new tab, with an outward arrow. */
  external?: boolean;
};

/** A link set as text: underlined in the accent, its arrow stepping forward on hover. */
export function TextLink({ href, children, external = false }: TextLinkProps) {
  const arrow = (
    <span aria-hidden="true" className="transition-transform duration-300 ease-(--ease-ui) group-hover:translate-x-1">
      {external ? "↗" : "→"}
    </span>
  );
  if (external) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className={STYLE}>
        {children}
        {arrow}
      </a>
    );
  }
  return (
    <Link href={href} className={STYLE}>
      {children}
      {arrow}
    </Link>
  );
}
