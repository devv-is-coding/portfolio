"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

/**
 * Renders its children everywhere except on `path`: e.g. the footer's "Let's build
 * something" link, which would point at the page the visitor is already on. Wrap it in
 * Suspense with the children as fallback (the URL is known only at request time on pages
 * with a dynamic segment).
 */
export function HiddenOn({ path, children }: { path: string; children: ReactNode }) {
  return usePathname() === path ? null : children;
}
