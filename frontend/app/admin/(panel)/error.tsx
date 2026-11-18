"use client";

import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Eyebrow } from "@/components/ui/eyebrow";

/**
 * An admin page couldn't load or an action failed unexpectedly (the API is down, a bug).
 * Production hides the message; the digest matches the server log line.
 */
export default function AdminError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div role="alert" className="flex max-w-xl flex-col items-start gap-6">
      <Eyebrow>Something went wrong</Eyebrow>
      <h1 className="font-display text-4xl font-extrabold uppercase">This page didn&apos;t load</h1>
      <p className="text-muted">
        The API may be unreachable for a moment. Try again; if it keeps failing, check that the backend is running.
      </p>
      {error.digest && <p className="font-mono text-xs text-muted">Reference: {error.digest}</p>}
      <div className="flex flex-wrap gap-3">
        <Button onClick={reset} size="sm">
          Try again
        </Button>
        <ButtonLink href="/admin" variant="outline" size="sm">
          Dashboard
        </ButtonLink>
      </div>
    </div>
  );
}
