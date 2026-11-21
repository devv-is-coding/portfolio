"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { cn } from "@/lib/cn";
import { unreadMessageCount } from "../_lib/unread";

// How often the unread count is checked while the admin stays on one page.
const UNREAD_CHECK_MS = 60_000;

const ITEMS = [
  { href: "/admin", label: "Dashboard" },
  { href: "/admin/messages", label: "Messages" },
  { href: "/admin/profile", label: "Profile" },
  { href: "/admin/projects", label: "Projects" },
  { href: "/admin/skills", label: "Skills" },
  { href: "/admin/experience", label: "Experience" },
  { href: "/admin/education", label: "Education" },
  { href: "/admin/certifications", label: "Certifications" },
  { href: "/admin/blog/posts", label: "Blog posts" },
  { href: "/admin/blog/categories", label: "Blog categories" },
  { href: "/admin/blog/tags", label: "Blog tags" },
  { href: "/admin/media", label: "Media" },
  { href: "/admin/settings", label: "Settings" },
] as const;

/**
 * Unread contact messages, checked on every page change, when the tab comes back into view and
 * once a minute. The menu stays mounted between admin pages, so it asks itself.
 */
function useUnreadCount(pathname: string): number {
  const [unread, setUnread] = useState(0);
  useEffect(() => {
    let active = true;
    const check = () => {
      if (document.visibilityState === "visible") {
        void unreadMessageCount().then((count) => {
          if (active && count !== null) {
            setUnread(count);
          }
        });
      }
    };
    check();
    const timer = window.setInterval(check, UNREAD_CHECK_MS);
    document.addEventListener("visibilitychange", check);
    return () => {
      active = false;
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", check);
    };
  }, [pathname]);
  return unread;
}

/** The admin sections; the current one is marked for sight and for screen readers. */
export function AdminNav() {
  const pathname = usePathname();
  const unread = useUnreadCount(pathname);

  return (
    <nav aria-label="Admin">
      <ul className="flex gap-1 overflow-x-auto md:flex-col">
        {ITEMS.map((item) => {
          const current = item.href === "/admin" ? pathname === item.href : pathname.startsWith(item.href);
          const dot = item.href === "/admin/messages" && unread > 0;
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                aria-current={current ? "page" : undefined}
                title={dot ? `${unread} unread` : undefined}
                className={cn(
                  "flex items-center gap-2 rounded-lg px-3 py-2 text-sm whitespace-nowrap transition-colors",
                  current ? "bg-accent text-accent-ink" : "text-muted hover:bg-paper/5 hover:text-paper",
                )}
              >
                {item.label}
                {dot && (
                  <>
                    <span aria-hidden="true" className="size-2 rounded-full bg-signal ring-2 ring-ink-raised" />
                    <span className="sr-only">({unread} unread)</span>
                  </>
                )}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
