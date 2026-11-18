/** Shown while an admin page loads its data from the API. */
export default function AdminLoading() {
  return (
    <div role="status" className="flex flex-col gap-4">
      <span className="sr-only">Loading…</span>
      <div className="h-10 w-64 animate-pulse rounded-lg bg-ink-raised" />
      <div className="h-32 w-full animate-pulse rounded-xl bg-ink-raised" />
    </div>
  );
}
