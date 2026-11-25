import { describe, expect, it } from "vitest";
import { currentNavHref, SITE } from "@/lib/site";

describe("currentNavHref", () => {
  it.each([
    ["/projects", "/projects"],
    ["/projects/marathon-timing", "/projects"],
    ["/blog/how-i-built-my-portfolio", "/blog"],
    ["/about", "/about"],
    ["/contact", "/contact"],
  ])("puts %s under %s", (pathname, expected) => {
    expect(currentNavHref(pathname)).toBe(expected);
  });

  it.each(["/", "/projectsx", "/admin", "/does-not-exist"])("marks nothing on %s", (pathname) => {
    expect(currentNavHref(pathname)).toBeNull();
  });
});

// Search engines cut longer ones off, and SEO audits flag shorter ones.
describe("home page title and description", () => {
  it("has a title of 50-60 characters that starts with the name", () => {
    expect(SITE.title.length).toBeGreaterThanOrEqual(50);
    expect(SITE.title.length).toBeLessThanOrEqual(60);
    expect(SITE.title.startsWith(SITE.name)).toBe(true);
  });

  it("has a description of 120-160 characters that names the person", () => {
    expect(SITE.description.length).toBeGreaterThanOrEqual(120);
    expect(SITE.description.length).toBeLessThanOrEqual(160);
    expect(SITE.description).toContain(SITE.name);
  });
});
