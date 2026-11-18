/** Refresh this long before the access token expires, so a request never carries a dead one. */
export const REFRESH_MARGIN_SECONDS = 60;

/**
 * When an access token (a JWT) expires, in seconds since the epoch, or null if it isn't a
 * readable JWT. Only the `exp` claim is read and nothing is verified: the API checks the
 * signature on every call. This only decides when to refresh.
 */
export function tokenExpiry(token: string): number | null {
  const payload = token.split(".")[1];
  if (!payload) {
    return null;
  }
  try {
    const claims: unknown = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
    const exp = typeof claims === "object" && claims !== null ? (claims as { exp?: unknown }).exp : undefined;
    return typeof exp === "number" ? exp : null;
  } catch {
    return null;
  }
}

/** True when the token is missing, unreadable, expired or expires within the refresh margin. */
export function needsRefresh(token: string | undefined, nowSeconds: number): boolean {
  const expiry = token ? tokenExpiry(token) : null;
  return expiry === null || expiry - nowSeconds <= REFRESH_MARGIN_SECONDS;
}
