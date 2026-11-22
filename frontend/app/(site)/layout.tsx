import { Suspense } from "react";
import { Motion } from "@/components/motion";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

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
    </>
  );
}
