import { describe, expect, it } from "vitest";
import { needsRefresh, REFRESH_MARGIN_SECONDS, tokenExpiry } from "@/lib/auth/tokens";

function jwt(claims: object): string {
  const part = (value: object) => Buffer.from(JSON.stringify(value)).toString("base64url");
  return `${part({ alg: "HS256", typ: "JWT" })}.${part(claims)}.signature`;
}

describe("tokenExpiry", () => {
  it("reads the exp claim", () => {
    expect(tokenExpiry(jwt({ sub: "1", exp: 1_800_000_000 }))).toBe(1_800_000_000);
  });

  it.each(["", "not-a-jwt", "a.%%%.c", jwt({ sub: "1" }), jwt({ exp: "soon" })])(
    "returns null for an unreadable token (%s)",
    (token) => {
      expect(tokenExpiry(token)).toBeNull();
    },
  );
});

describe("needsRefresh", () => {
  const now = 1_800_000_000;

  it("keeps a token that is valid beyond the margin", () => {
    expect(needsRefresh(jwt({ exp: now + REFRESH_MARGIN_SECONDS + 1 }), now)).toBe(false);
  });

  it.each([
    ["expiring within the margin", jwt({ exp: now + REFRESH_MARGIN_SECONDS })],
    ["expired", jwt({ exp: now - 1 })],
    ["unreadable", "garbage"],
    ["missing", undefined],
  ])("refreshes a token that is %s", (_case, token) => {
    expect(needsRefresh(token, now)).toBe(true);
  });
});
