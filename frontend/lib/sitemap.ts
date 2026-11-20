import "server-only";
import type { MetadataRoute } from "next";
import type { Page } from "@/lib/api/public";
import { getPosts, getProjects } from "@/lib/api/public";
import { parseApiDate } from "@/lib/format";
import { SITE } from "@/lib/site";

const STATIC_PATHS = ["/", "/projects", "/about", "/blog", "/contact"] as const;

// The API's largest page size.
const PAGE_SIZE = 100;

/** Every page of a public list, read with the same cached readers the pages use. */
async function readAll<T>(
  read: (page: number) => Promise<Page<T>>,
): Promise<T[]> {
  const first = await read(1);
  const rest = await Promise.all(
    Array.from({ length: Math.max(first.pages - 1, 0) }, (_, index) =>
      read(index + 2),
    ),
  );
  return [first, ...rest].flatMap((page) => page.items);
}

function lastModified(publishedAt: string | null): Date | undefined {
  return publishedAt ? parseApiDate(publishedAt) : undefined;
}

/**
 * The fixed pages plus every published project and post (drafts and archived ones never
 * reach the public API), as absolute URLs on the production domain.
 */
export async function sitemapEntries(): Promise<MetadataRoute.Sitemap> {
  const [projects, posts] = await Promise.all([
    readAll((page) => getProjects({ page, size: PAGE_SIZE })),
    readAll((page) => getPosts({ page, size: PAGE_SIZE })),
  ]);
  return [
    ...STATIC_PATHS.map((path) => ({ url: new URL(path, SITE.url).href })),
    ...projects.map((project) => ({
      url: `${SITE.url}/projects/${project.slug}`,
      lastModified: lastModified(project.published_at),
    })),
    ...posts.map((post) => ({
      url: `${SITE.url}/blog/${post.slug}`,
      lastModified: lastModified(post.published_at),
    })),
  ];
}
