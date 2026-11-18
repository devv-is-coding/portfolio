import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiClient, unwrap } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";

type Call = { url: string; headers: Headers };

function stubFetch(answer: () => Response | Promise<Response>): Call[] {
  const calls: Call[] = [];
  vi.stubGlobal("fetch", async (request: Request) => {
    calls.push({ url: request.url, headers: request.headers });
    return answer();
  });
  return calls;
}

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  vi.stubEnv("API_URL", "http://api.test");
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("apiClient", () => {
  it("calls API_URL and returns the typed data", async () => {
    const calls = stubFetch(() => json(200, { status: "ok" }));

    const health = await unwrap(apiClient().GET("/health"));

    expect(health).toEqual({ status: "ok" });
    expect(calls[0]?.url).toBe("http://api.test/health");
  });

  it("sends the access token and the visitor IP when given", async () => {
    const calls = stubFetch(() => json(200, { id: 1, email: "me@example.com" }));

    await unwrap(apiClient({ accessToken: "token-1", clientIp: "203.0.113.7" }).GET("/auth/me"));

    expect(calls[0]?.headers.get("Authorization")).toBe("Bearer token-1");
    expect(calls[0]?.headers.get("X-Forwarded-For")).toBe("203.0.113.7");
  });

  it("sends neither header by default", async () => {
    const calls = stubFetch(() => json(200, { status: "ok" }));

    await unwrap(apiClient().GET("/health"));

    expect(calls[0]?.headers.has("Authorization")).toBe(false);
    expect(calls[0]?.headers.has("X-Forwarded-For")).toBe(false);
  });

  it("refuses to run without API_URL", () => {
    vi.stubEnv("API_URL", "");

    expect(() => apiClient()).toThrow(/API_URL/);
  });
});

describe("unwrap", () => {
  it("throws the API's error for a failed answer", async () => {
    stubFetch(() =>
      json(404, { error: { code: "not_found", message: "Project not found.", details: null } }),
    );

    const failure = unwrap(
      apiClient().GET("/projects/{slug}", { params: { path: { slug: "missing" } } }),
    );

    await expect(failure).rejects.toMatchObject({ status: 404, code: "not_found" });
  });

  it("throws api_unreachable when the request gets no answer", async () => {
    stubFetch(() => {
      throw new TypeError("fetch failed");
    });

    const failure = unwrap(apiClient().GET("/health"));

    await expect(failure).rejects.toBeInstanceOf(ApiError);
    await expect(failure).rejects.toMatchObject({ status: 503, code: "api_unreachable" });
  });

  it("returns nothing for 204 No Content", async () => {
    stubFetch(() => new Response(null, { status: 204 }));

    const result = await unwrap(
      apiClient({ accessToken: "token-1" }).DELETE("/admin/skills/{skill_id}", {
        params: { path: { skill_id: 1 } },
      }),
    );

    expect(result).toBeUndefined();
  });
});
