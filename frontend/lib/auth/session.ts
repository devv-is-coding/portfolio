import "server-only";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { apiClient, type ApiClient, type ApiResult, unwrap } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { ACCESS_COOKIE } from "@/lib/auth/cookies";
import { LOGIN_PATH } from "@/lib/auth/paths";
import { clientIp } from "@/lib/request";

/**
 * Runs an admin API call with the session's access token (refreshed for this request by
 * proxy.ts). Without a session, or when the API refuses it (401: revoked, expired), it sends
 * the visitor to the login page. Every admin read and Server Action goes through here, so
 * each checks the session itself instead of trusting the proxy alone.
 */
export async function asAdmin<T>(call: (api: ApiClient) => Promise<ApiResult<T>>): Promise<T> {
  const accessToken = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (!accessToken) {
    redirect(LOGIN_PATH);
  }
  try {
    return await unwrap(call(apiClient({ accessToken, clientIp: await clientIp() })));
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      redirect(LOGIN_PATH);
    }
    throw error;
  }
}

/** The signed-in admin's account. */
export function currentAdmin() {
  return asAdmin((api) => api.GET("/auth/me"));
}
