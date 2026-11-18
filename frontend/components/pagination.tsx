import { ButtonLink } from "@/components/ui/button-link";

type PaginationProps = {
  page: number;
  pages: number;
  /** Builds the link to a page, keeping the list's other filters. */
  href: (page: number) => string;
};

/** Previous and next links with the position in between; nothing when there's one page. */
export function Pagination({ page, pages, href }: PaginationProps) {
  if (pages <= 1) {
    return null;
  }
  return (
    <nav aria-label="Pagination" className="flex items-center justify-between gap-4">
      {page > 1 ? (
        <ButtonLink href={href(page - 1)} variant="outline" size="sm" rel="prev">
          ← Previous
        </ButtonLink>
      ) : (
        <span />
      )}
      <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted">
        Page {page} of {pages}
      </p>
      {page < pages ? (
        <ButtonLink href={href(page + 1)} variant="outline" size="sm" rel="next">
          Next →
        </ButtonLink>
      ) : (
        <span />
      )}
    </nav>
  );
}
