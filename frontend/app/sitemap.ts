import type { MetadataRoute } from "next";
import { readAtRequestTimeWithoutApi } from "@/lib/api/public";
import { sitemapEntries } from "@/lib/sitemap";

/**
 * /sitemap.xml. Cached like the pages (the readers' projects and blog tags), so an admin
 * publish updates it too.
 */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  await readAtRequestTimeWithoutApi();
  return sitemapEntries();
}
