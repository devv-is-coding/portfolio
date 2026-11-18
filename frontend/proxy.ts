import { type NextRequest, NextResponse } from "next/server";
import { ApiError } from "@/lib/api/errors";
import { ACCESS_COOKIE, REFRESH_COOKIE, sessionCookies } from "@/lib/auth/cookies";
import { ADMIN_HOME, LOGIN_PATH } from "@/lib/auth/paths";
import { refreshTokens } from "@/lib/auth/refresh";
import { needsRefresh } from "@/lib/auth/tokens";

/**
 * Guards /admin: without a session the visitor goes to the login page, and an access token
 * that is about to expire is refreshed here, the one place that can set cookies before the
 * page renders. This is the first line only: every admin read and Server Action checks the
 * session again (lib/auth/session.ts).
 */
export async function proxy(request: NextRequest) {
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;

  if (request.nextUrl.pathname === LOGIN_PATH) {
    return refreshToken
      ? NextResponse.redirect(new URL(ADMIN_HOME, request.url))
      : NextResponse.next();
  }
  if (!needsRefresh(request.cookies.get(ACCESS_COOKIE)?.value, Date.now() / 1000)) {
    return NextResponse.next();
  }
  if (!refreshToken) {
    return toLogin(request);
  }

  try {
    const cookies = sessionCookies(await refreshTokens(refreshToken));
    // On the request too, so this very render already uses the new access token.
    for (const cookie of cookies) {
      request.cookies.set(cookie.name, cookie.value);
    }
    const response = NextResponse.next({ request });
    for (const cookie of cookies) {
      response.cookies.set(cookie);
    }
    return response;
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return toLogin(request);
    }
    // The API is down: keep the session and let the page show its error.
    return NextResponse.next();
  }
}

function toLogin(request: NextRequest): NextResponse {
  const url = new URL(LOGIN_PATH, request.url);
  url.searchParams.set("next", request.nextUrl.pathname + request.nextUrl.search);
  const response = NextResponse.redirect(url);
  response.cookies.delete(ACCESS_COOKIE);
  response.cookies.delete(REFRESH_COOKIE);
  return response;
}

export const config = {
  matcher: ["/admin/:path*"],
};
