import type { ReactNode } from "react";

/** What a list shows when it has nothing yet. */
export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded-card border border-dashed border-line px-6 py-12 text-center">
      <p className="font-display text-2xl">{title}</p>
      {children && <div className="mt-3 text-muted">{children}</div>}
    </div>
  );
}
