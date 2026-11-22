import { Suspense } from "react";
import { Motion } from "@/components/motion";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

// Vercel sets VERCEL=1 for its builds and deployments; elsewhere (local, Docker, CI) the
// /_vercel/ scripts don't exist.
const ON_VERCEL = process.env.VERCEL === "1";

/** The public site's frame: header, the page (target of the skip link), footer and motion. */
export default function SiteLayout({ children }: LayoutProps<"/">) {
  return (
    <>
      <SiteHeader />
      <main id="main" className="flex-1">
        {children}
      </main>
      <SiteFooter />
      {/* Motion reads the URL (usePathname), which only exists at request time: in a boundary,
          so pages still prerender. It renders nothing, so there's no fallback to show. */}
      <Suspense>
        <Motion />
      </Suspense>
      {/* Vercel Web Analytics (visitors, page views) and Speed Insights (real visitors' Core
          Web Vitals), as Vercel's plain script tags: the React components added 3.4 KB to
          every page and broke the JavaScript budget. They track navigations themselves, load
          async from the site's own /_vercel/ paths (allowed by the CSP), and sit here rather
          than in the root layout, so the admin's own visits aren't counted. */}
      {ON_VERCEL && (
        <>
          <script async src="/_vercel/insights/script.js" />
          <script async src="/_vercel/speed-insights/script.js" />
        </>
      )}
    </>
  );
}
