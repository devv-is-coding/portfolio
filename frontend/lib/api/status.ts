import "server-only";
import { apiClient, unwrap } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";

/** What a visitor is told when a page can't load: up, the database down, or the API down. */
export type ServiceStatus = "ok" | "database_down" | "api_down";

/** The API's message when MariaDB can't be reached (`/health` and every other endpoint). */
export const DATABASE_UNAVAILABLE = "Database unavailable";

// A cold start (FastAPI Cloud scales to zero, the free database sleeps) takes a few seconds.
const HEALTH_TIMEOUT_MS = 10_000;

/** Whether the error is the API saying the database is down (503 "Database unavailable"). */
export function isDatabaseDown(error: unknown): boolean {
  return error instanceof ApiError && error.status === 503 && error.message === DATABASE_UNAVAILABLE;
}

/** Asks the API's `/health`, which checks the database. Never cached. */
export async function serviceStatus(): Promise<ServiceStatus> {
  try {
    await unwrap(apiClient().GET("/health", { cache: "no-store", signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS) }));
    return "ok";
  } catch (error) {
    return isDatabaseDown(error) ? "database_down" : "api_down";
  }
}
