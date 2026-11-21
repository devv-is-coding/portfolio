import "server-only";
import { redirect } from "next/navigation";
import { listHref } from "@/lib/search-params";

/** Rows per page on the admin lists. */
export const ADMIN_PAGE_SIZE = 25;

type ListPage = { page: number; pages: number };

/**
 * Sends a page past the end (the last item of the last page deleted, an edited URL) to the
 * last page that exists, so the list never says "nothing yet" while it has items.
 */
export function keepPageInRange(list: ListPage, path: string, params: Record<string, string | undefined> = {}): void {
  if (list.page > 1 && list.page > list.pages) {
    redirect(listHref(path, { ...params, page: Math.max(list.pages, 1) }));
  }
}
