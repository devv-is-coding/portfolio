import { describe, expect, it } from "vitest";
import { ADMIN_HOME, LOGIN_PATH, safeNextPath } from "@/lib/auth/paths";

describe("safeNextPath", () => {
  it.each(["/admin", "/admin/projects", "/admin/projects?status=draft", "/admin/blog/posts/3"])(
    "keeps an admin path (%s)",
    (path) => {
      expect(safeNextPath(path)).toBe(path);
    },
  );

  it.each([
    null,
    undefined,
    42,
    "",
    "/",
    "/projects",
    "https://evil.example/admin",
    "//evil.example/admin",
    "/admin//evil.example",
    "/admin/\\evil.example",
    "/administrator",
    "/admin/ projects",
    LOGIN_PATH,
  ])("falls back to the dashboard for %j", (next) => {
    expect(safeNextPath(next)).toBe(ADMIN_HOME);
  });
});
