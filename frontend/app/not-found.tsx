import type { Metadata } from "next";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { ButtonLink } from "@/components/ui/button-link";
import { Container } from "@/components/ui/container";
import { Eyebrow } from "@/components/ui/eyebrow";

export const metadata: Metadata = {
  title: "Page not found",
};

// Rendered outside the (site) layout (unknown URLs and notFound() both end up here), so it
// brings the site's header and footer itself.
export default function NotFound() {
  return (
    <>
      <SiteHeader />
      <main id="main" className="flex-1">
        <Container className="flex flex-col items-start gap-8 py-24 sm:py-32">
          <Eyebrow>Error 404</Eyebrow>
          <h1 className="font-display text-headline font-extrabold uppercase">
            Nothing <span className="text-accent">here.</span>
          </h1>
          <p className="max-w-md text-lg text-muted">
            This page doesn&apos;t exist, or not yet. The home page does.
          </p>
          <ButtonLink href="/">Back home</ButtonLink>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
