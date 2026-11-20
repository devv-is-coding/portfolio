import type { MetadataRoute } from "next";
import { SITE } from "@/lib/site";

/** Crawlers may read every public page; the admin and the internal status route stay out. */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/", disallow: ["/admin", "/api/"] },
    sitemap: `${SITE.url}/sitemap.xml`,
  };
}
