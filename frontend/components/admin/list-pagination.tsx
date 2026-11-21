import { Pagination } from "@/components/pagination";
import { listHref } from "@/lib/search-params";

type ListPaginationProps = {
  /** The list's own path, e.g. `/admin/projects`. */
  path: string;
  list: { page: number; pages: number };
  /** The list's filters, kept on every page link. */
  params?: Record<string, string | undefined>;
};

/** Previous / next links under an admin list; nothing when it fits one page. */
export function ListPagination({ path, list, params = {} }: ListPaginationProps) {
  return (
    <div className="mt-8">
      <Pagination page={list.page} pages={list.pages} href={(page) => listHref(path, { ...params, page })} />
    </div>
  );
}
