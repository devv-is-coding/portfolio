"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";

const ITEMS = [{ href: "/admin", label: "Dashboard" }] as const;

/** The admin sections; the current one is marked for sight and for screen readers. */
export function AdminNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="Admin">
      <ul className="flex gap-1 overflow-x-auto md:flex-col">
        {ITEMS.map((item) => {
          const current = item.href === "/admin" ? pathname === item.href : pathname.startsWith(item.href);
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                aria-current={current ? "page" : undefined}
                className={cn(
                  "block rounded-lg px-3 py-2 text-sm whitespace-nowrap transition-colors",
                  current ? "bg-accent text-accent-ink" : "text-muted hover:bg-paper/5 hover:text-paper",
                )}
              >
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
