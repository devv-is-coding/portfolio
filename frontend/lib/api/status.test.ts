import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, unreachableError } from "@/lib/api/errors";
import { isDatabaseDown, serviceStatus } from "@/lib/api/status";

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const databaseDown = { error: { code: "service_unavailable", message: "Database unavailable", details: null } };

beforeEach(() => {
  vi.stubEnv("API_URL", "http://api.test");
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("serviceStatus", () => {
  it("is ok when /health answers 200", async () => {
    const urls: string[] = [];
    vi.stubGlobal("fetch", async (request: Request) => {
      urls.push(request.url);
      return json(200, { status: "ok" });
    });

    expect(await serviceStatus()).toBe("ok");
    expect(urls).toEqual(["http://api.test/health"]);
  });

  it("reports the database down when /health says so", async () => {
    vi.stubGlobal("fetch", async () => json(503, databaseDown));

    expect(await serviceStatus()).toBe("database_down");
  });

  it("reports the API down when it can't be reached", async () => {
    vi.stubGlobal("fetch", async () => {
      throw new TypeError("fetch failed");
    });

    expect(await serviceStatus()).toBe("api_down");
  });

  it("reports the API down when it answers something else", async () => {
    vi.stubGlobal("fetch", async () => new Response("Bad gateway", { status: 502 }));

    expect(await serviceStatus()).toBe("api_down");
  });
});

describe("isDatabaseDown", () => {
  it("is true only for the API's 503 Database unavailable", () => {
    expect(isDatabaseDown(new ApiError(503, databaseDown.error))).toBe(true);
    expect(isDatabaseDown(new ApiError(503, { code: "service_unavailable", message: "ImageKit is not configured" }))).toBe(false);
    expect(isDatabaseDown(unreachableError())).toBe(false);
    expect(isDatabaseDown(new Error("Database unavailable"))).toBe(false);
  });
});
