"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Suspense } from "react";
import { cn } from "@/lib/cn";
import { currentNavHref, NAV_ITEMS, type NavHref } from "@/lib/site";

type NavLinksProps = {
  className: string;
  /** Classes every link has. */
  linkClassName: string;
  /** Classes of the links to other sections. */
  idleClassName?: string;
  /** Classes of the link to the section the visitor is in. */
  currentClassName: string;
  onNavigate?: () => void;
};

/**
 * The main menu's links, the current section marked for sight and for screen readers
 * (`aria-current`). The URL is known only at request time on pages with a dynamic segment
 * (a project, a post), so it is read inside a boundary whose fallback is the same list
 * unmarked: the rest of the page still prerenders and nothing moves when the mark appears.
 */
export function NavLinks(props: NavLinksProps) {
  return (
    <Suspense fallback={<NavList current={null} {...props} />}>
      <CurrentNavList {...props} />
    </Suspense>
  );
}

function CurrentNavList(props: NavLinksProps) {
  return <NavList current={currentNavHref(usePathname())} {...props} />;
}

function NavList({
  current,
  className,
  linkClassName,
  idleClassName,
  currentClassName,
  onNavigate,
}: NavLinksProps & { current: NavHref | null }) {
  return (
    <ul className={className}>
      {NAV_ITEMS.map((item) => {
        const isCurrent = item.href === current;
        return (
          <li key={item.href}>
            <Link
              href={item.href}
              onClick={onNavigate}
              aria-current={isCurrent ? "page" : undefined}
              className={cn(linkClassName, isCurrent ? currentClassName : idleClassName)}
            >
              {item.label}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
