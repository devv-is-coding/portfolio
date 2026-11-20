import "server-only";
import createClient from "openapi-fetch";
import { toApiError, unreachableError } from "@/lib/api/errors";
import type { paths } from "@/lib/api/schema";

type ClientOptions = {
  /** The admin's access token, for `/admin` routes and `/auth/me`. */
  accessToken?: string;
  /** The visitor's IP, so the API's per-IP limits (login, contact) see the visitor, not this server. */
  clientIp?: string;
};

/**
 * A typed client for the FastAPI backend, for server code only: the browser never talks to
 * the API directly (tokens stay in httpOnly cookies on this server). Paths, parameters and
 * bodies are checked against the types generated from `/openapi.json` (`npm run api:types`).
 */
export function apiClient({ accessToken, clientIp }: ClientOptions = {}) {
  const baseUrl = process.env.API_URL;
  if (!baseUrl) {
    throw new Error("API_URL is not set (see frontend/.env.example).");
  }
  const headers: Record<string, string> = {};
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }
  if (clientIp) {
    headers["X-Forwarded-For"] = clientIp;
  }
  // A production API answers only callers with this key (development doesn't check it).
  const frontendKey = process.env.FRONTEND_API_KEY;
  if (frontendKey) {
    headers["X-Frontend-Key"] = frontendKey;
  }
  return createClient<paths>({ baseUrl, headers });
}

export type ApiClient = ReturnType<typeof apiClient>;

export type ApiResult<T> = { data?: T; error?: unknown; response: Response };

/**
 * Waits for a client call and returns its data, or throws an ApiError: the API's own error
 * for a failed answer, `api_unreachable` (503) when the request never got an answer.
 */
export async function unwrap<T>(request: Promise<ApiResult<T>>): Promise<T> {
  let result: ApiResult<T>;
  try {
    result = await request;
  } catch {
    throw unreachableError();
  }
  if (!result.response.ok) {
    throw toApiError(result.response.status, result.error);
  }
  return result.data as T;
}
