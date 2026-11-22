import type { Metadata } from "next";
import { NotFoundMessage } from "@/components/not-found-message";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "Page not found",
};

// Unknown URLs are rendered outside the (site) layout, so this page brings the site's header
// and footer itself. notFound() inside a site page uses app/(site)/not-found.tsx instead.
export default function NotFound() {
  return (
    <>
      <SiteHeader />
      <main id="main" className="flex-1">
        <NotFoundMessage />
      </main>
      <SiteFooter />
    </>
  );
}
