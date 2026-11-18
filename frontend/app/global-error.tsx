"use client";

import "./globals.css";

/**
 * The last resort: the root layout itself failed, so this page brings its own <html>. It
 * keeps to system fonts and plain markup, so it renders whatever broke.
 */
export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="en">
      <body className="flex min-h-svh items-center bg-ink px-5 text-paper">
        <main className="mx-auto flex max-w-xl flex-col items-start gap-6">
          <h1 className="text-4xl font-extrabold uppercase">Something went wrong</h1>
          <p className="text-muted">The site couldn&apos;t load. Please try again in a moment.</p>
          <button type="button" onClick={reset} className="rounded-full bg-accent px-6 py-3 font-semibold text-accent-ink">
            Try again
          </button>
        </main>
      </body>
    </html>
  );
}
