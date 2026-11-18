import "server-only";
import { apiClient, unwrap } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

type TokenResponse = components["schemas"]["TokenResponse"];

// A refresh answer is reused for this long: requests that left the browser with the old
// refresh token (parallel prefetches, a second tab) get the same new pair.
const REUSE_WINDOW_MS = 30_000;

const recent = new Map<string, { tokens: Promise<TokenResponse>; until: number }>();

/**
 * Exchanges a refresh token for a new pair, at most once per token in this server process.
 *
 * The API rotates refresh tokens and treats a second use as theft (it then revokes every
 * session). Admin pages fire several requests at once, so without this two of them could
 * refresh the same token and log the admin out. With several server instances this guard is
 * per instance (open decision D9: a short grace period in the API).
 */
export function refreshTokens(refreshToken: string): Promise<TokenResponse> {
  const now = Date.now();
  for (const [token, entry] of recent) {
    if (entry.until <= now) {
      recent.delete(token);
    }
  }
  const known = recent.get(refreshToken);
  if (known) {
    return known.tokens;
  }
  const tokens = unwrap(apiClient().POST("/auth/refresh", { body: { refresh_token: refreshToken } }));
  recent.set(refreshToken, { tokens, until: now + REUSE_WINDOW_MS });
  // A failed refresh must not be reused: the next attempt (after a fix, a retry) asks again.
  tokens.catch(() => recent.delete(refreshToken));
  return tokens;
}
