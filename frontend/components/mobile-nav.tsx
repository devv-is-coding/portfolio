"use client";

import Link from "next/link";
import { useEffect, useId, useState } from "react";
import { cn } from "@/lib/cn";
import { NAV_ITEMS } from "@/lib/site";

/** The menu below the `md` breakpoint: a full-screen panel, closed by a link, the button or Escape. */
export function MobileNav() {
  const [open, setOpen] = useState(false);
  const panelId = useId();

  useEffect(() => {
    if (!open) {
      return;
    }
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [open]);

  return (
    <div className="md:hidden">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((isOpen) => !isOpen)}
        className="relative z-20 flex size-11 items-center justify-center rounded-full border border-paper/25"
      >
        <span className="sr-only">{open ? "Close menu" : "Open menu"}</span>
        <span aria-hidden="true" className="flex w-5 flex-col gap-1.5">
          <span
            className={cn(
              "h-0.5 bg-paper transition-transform duration-300",
              open && "translate-y-1 rotate-45",
            )}
          />
          <span
            className={cn(
              "h-0.5 bg-paper transition-transform duration-300",
              open && "-translate-y-1 -rotate-45",
            )}
          />
        </span>
      </button>
      <nav
        id={panelId}
        aria-label="Main"
        hidden={!open}
        className="fixed inset-0 z-10 overflow-y-auto bg-ink px-5 pt-24 pb-10"
      >
        <ul className="flex flex-col gap-2">
          {NAV_ITEMS.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                onClick={() => setOpen(false)}
                className="block py-2 font-display text-headline font-extrabold uppercase hover:text-accent"
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
