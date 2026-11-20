"use client";

import { useEffect, useState } from "react";
import type { ServiceStatus } from "@/lib/api/status";

const OUTAGE_MESSAGES: Record<Exclude<ServiceStatus, "ok">, string> = {
  database_down: "My database is offline right now, so this can't load. Please check back in a few minutes.",
  api_down: "My server is offline right now, so this can't load. Please check back in a few minutes.",
};

type OutageMessageProps = {
  /** Shown while checking, and when the API and database are up (another kind of failure). */
  fallback: string;
  className?: string;
};

/**
 * Why something failed to load, in words a visitor understands: asks `/api/status` once and
 * says when the database or the server is offline. Only rendered by error screens.
 */
export function OutageMessage({ fallback, className }: OutageMessageProps) {
  const [status, setStatus] = useState<ServiceStatus>("ok");

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/status", { cache: "no-store", signal: controller.signal })
      .then((response) => response.json() as Promise<{ status: ServiceStatus }>)
      .then((body) => setStatus(body.status))
      .catch(() => {
        // No answer from this site either: keep the fallback.
      });
    return () => controller.abort();
  }, []);

  return (
    <p role="status" className={className}>
      {status === "ok" ? fallback : OUTAGE_MESSAGES[status]}
    </p>
  );
}
