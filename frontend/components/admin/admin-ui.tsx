import Link from "next/link";
import type { ReactNode } from "react";
import { EmptyState } from "@/components/ui/empty-state";
import { Eyebrow } from "@/components/ui/eyebrow";

type PageHeaderProps = {
  eyebrow: string;
  title: string;
  /** e.g. a "New skill" button or a delete button. */
  action?: ReactNode;
  back?: { href: string; label: string };
};

export function PageHeader({ eyebrow, title, action, back }: PageHeaderProps) {
  return (
    <header className="mb-8 flex flex-col gap-4">
      {back && (
        <Link href={back.href} className="w-fit font-mono text-xs uppercase tracking-[0.2em] text-muted hover:text-accent">
          ← {back.label}
        </Link>
      )}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-3">
          <Eyebrow>{eyebrow}</Eyebrow>
          <h1 className="font-display text-4xl font-extrabold uppercase">{title}</h1>
        </div>
        {action}
      </div>
    </header>
  );
}

export type Column<T> = { label: string; value: (item: T) => ReactNode };

type DataTableProps<T extends { id: number }> = {
  items: readonly T[];
  columns: readonly Column<T>[];
  /** Each row's first cell links to the item's edit page. */
  href: (item: T) => string;
  empty: string;
};

/** A list of items; the first column links to each item. */
export function DataTable<T extends { id: number }>({ items, columns, href, empty }: DataTableProps<T>) {
  if (items.length === 0) {
    return <EmptyState title={empty} />;
  }
  return (
    <div className="overflow-x-auto rounded-2xl border border-line">
      <table className="w-full text-left text-sm">
        <thead className="bg-ink-raised font-mono text-xs uppercase tracking-[0.15em] text-muted">
          <tr>
            {columns.map((column) => (
              <th key={column.label} scope="col" className="px-4 py-3 font-normal">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="border-t border-line">
              {columns.map((column, index) => (
                <td key={column.label} className="px-4 py-3">
                  {index === 0 ? (
                    <Link href={href(item)} className="font-semibold hover:text-accent">
                      {column.value(item)}
                    </Link>
                  ) : (
                    column.value(item)
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
