"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { apiClient, unwrap } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { ACCESS_COOKIE, REFRESH_COOKIE, sessionCookies } from "@/lib/auth/cookies";
import { LOGIN_PATH, safeNextPath } from "@/lib/auth/paths";
import { clientIp } from "@/lib/request";

export type LoginState = { error?: string; email?: string };

function loginErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return "Wrong email or password.";
    }
    if (error.status === 422) {
      return "Enter a valid email address and your password.";
    }
    return error.message; // 429 (too many attempts) and 503 explain themselves
  }
  return "Logging in failed. Please try again.";
}

/** Logs in with the API and keeps the tokens in httpOnly cookies on this server. */
export async function login(_state: LoginState, formData: FormData): Promise<LoginState> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  if (!email || !password) {
    return { error: "Enter your email and password.", email };
  }
  let tokens;
  try {
    tokens = await unwrap(
      apiClient({ clientIp: await clientIp() }).POST("/auth/login", { body: { email, password } }),
    );
  } catch (error) {
    return { error: loginErrorMessage(error), email };
  }
  const store = await cookies();
  for (const cookie of sessionCookies(tokens)) {
    store.set(cookie);
  }
  redirect(safeNextPath(formData.get("next")));
}

/** Revokes the refresh token in the API, clears the cookies and returns to the login page. */
export async function logout(): Promise<void> {
  const store = await cookies();
  const refreshToken = store.get(REFRESH_COOKIE)?.value;
  if (refreshToken) {
    try {
      await unwrap(
        apiClient({ clientIp: await clientIp() }).POST("/auth/logout", {
          body: { refresh_token: refreshToken },
        }),
      );
    } catch (error) {
      // The cookies go anyway; the token then simply expires in the API.
      console.warn("Logout: the API didn't revoke the refresh token.", error);
    }
  }
  store.delete(ACCESS_COOKIE);
  store.delete(REFRESH_COOKIE);
  redirect(LOGIN_PATH);
}
