import "server-only";
import type { components } from "@/lib/api/schema";

type TokenResponse = components["schemas"]["TokenResponse"];

export const ACCESS_COOKIE = "pf_access";
export const REFRESH_COOKIE = "pf_refresh";

// Matches the API's REFRESH_TOKEN_EXPIRE_DAYS (30): the API refuses an older token anyway.
const REFRESH_MAX_AGE_SECONDS = 30 * 24 * 60 * 60;

/** A cookie in the shape both `cookies().set()` and `NextResponse.cookies.set()` accept. */
export type SessionCookie = {
  name: typeof ACCESS_COOKIE | typeof REFRESH_COOKIE;
  value: string;
  maxAge: number;
  // httpOnly: browser JavaScript never sees a token. Lax: sent on normal navigation.
  httpOnly: true;
  sameSite: "lax";
  secure: boolean;
  path: "/";
};

/** The two cookies that hold an admin session. */
export function sessionCookies(tokens: TokenResponse): SessionCookie[] {
  const base = {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
  } as const;
  return [
    { ...base, name: ACCESS_COOKIE, value: tokens.access_token, maxAge: tokens.expires_in },
    { ...base, name: REFRESH_COOKIE, value: tokens.refresh_token, maxAge: REFRESH_MAX_AGE_SECONDS },
  ];
}
