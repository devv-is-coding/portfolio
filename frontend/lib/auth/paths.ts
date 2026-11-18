export const ADMIN_HOME = "/admin";
export const LOGIN_PATH = "/admin/login";

/**
 * Where to go after logging in: the admin page the visitor was sent away from, or the
 * dashboard. Only paths inside /admin are allowed, so the login page can't be used to send
 * someone to another site (`//evil.example`, `/\evil.example`, absolute URLs).
 */
export function safeNextPath(next: unknown): string {
  if (typeof next !== "string" || !next.startsWith(ADMIN_HOME) || next === LOGIN_PATH) {
    return ADMIN_HOME;
  }
  const rest = next.slice(ADMIN_HOME.length);
  if (rest !== "" && !rest.startsWith("/") && !rest.startsWith("?")) {
    return ADMIN_HOME; // e.g. /administrator
  }
  return /[\\\s]|\/\//.test(next) ? ADMIN_HOME : next;
}
