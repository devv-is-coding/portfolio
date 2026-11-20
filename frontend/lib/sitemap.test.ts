import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Page } from "@/lib/api/public";
import { getPosts, getProjects } from "@/lib/api/public";
import { sitemapEntries } from "@/lib/sitemap";

vi.mock("@/lib/api/public", () => ({
  getProjects: vi.fn(),
  getPosts: vi.fn(),
}));

type Item = { slug: string; published_at: string | null };

/**
 * Answers like the API: the asked page of `items`, `size` per page. Typed as a page of
 * `never` so it stands in for both readers (only slug and published_at are read).
 */
function pagedReader(items: Item[], size: number) {
  return async ({ page = 1 }: { page?: number } = {}): Promise<
    Page<never>
  > => ({
    items: items.slice((page - 1) * size, page * size) as never[],
    total: items.length,
    page,
    size,
    pages: Math.ceil(items.length / size),
  });
}

function items(prefix: string, count: number): Item[] {
  return Array.from({ length: count }, (_, index) => ({
    slug: `${prefix}-${index + 1}`,
    published_at: "2026-03-01T10:00:00",
  }));
}

const STATIC_URLS = [
  "https://bendanodevinp.online/",
  "https://bendanodevinp.online/projects",
  "https://bendanodevinp.online/about",
  "https://bendanodevinp.online/blog",
  "https://bendanodevinp.online/contact",
];

describe("sitemapEntries", () => {
  beforeEach(() => {
    vi.mocked(getProjects).mockReset();
    vi.mocked(getPosts).mockReset();
  });

  it("lists only the fixed pages when nothing is published", async () => {
    vi.mocked(getProjects).mockImplementation(pagedReader([], 100));
    vi.mocked(getPosts).mockImplementation(pagedReader([], 100));

    const entries = await sitemapEntries();

    expect(entries.map((entry) => entry.url)).toEqual(STATIC_URLS);
  });

  it("adds every project and post, reading all pages of each list", async () => {
    vi.mocked(getProjects).mockImplementation(
      pagedReader(items("project", 250), 100),
    );
    vi.mocked(getPosts).mockImplementation(pagedReader(items("post", 3), 100));

    const urls = (await sitemapEntries()).map((entry) => entry.url);

    expect(urls).toHaveLength(5 + 250 + 3);
    expect(urls).toContain("https://bendanodevinp.online/projects/project-1");
    expect(urls).toContain("https://bendanodevinp.online/projects/project-250");
    expect(urls.slice(-3)).toEqual([
      "https://bendanodevinp.online/blog/post-1",
      "https://bendanodevinp.online/blog/post-2",
      "https://bendanodevinp.online/blog/post-3",
    ]);
    expect(vi.mocked(getProjects).mock.calls.map(([query]) => query)).toEqual([
      { page: 1, size: 100 },
      { page: 2, size: 100 },
      { page: 3, size: 100 },
    ]);
  });

  it("dates entries by their publish time in UTC, and leaves undated ones without", async () => {
    const project: Item = {
      slug: "dated",
      published_at: "2026-03-01T10:00:00",
    };
    const post: Item = { slug: "undated", published_at: null };
    vi.mocked(getProjects).mockImplementation(pagedReader([project], 100));
    vi.mocked(getPosts).mockImplementation(pagedReader([post], 100));

    const entries = await sitemapEntries();

    expect(entries.at(-2)?.lastModified).toEqual(
      new Date("2026-03-01T10:00:00Z"),
    );
    expect(entries.at(-1)?.lastModified).toBeUndefined();
  });
});
