import Link from "next/link";
import { MobileNav } from "@/components/mobile-nav";
import { NavLinks } from "@/components/nav-links";
import { Container } from "@/components/ui/container";
import { SITE } from "@/lib/site";

export function SiteHeader() {
  return (
    // Named, so page transitions leave it in place (globals.css).
    <header style={{ viewTransitionName: "site-header" }} className="sticky top-0 z-30 border-b border-line">
      {/* Frosted glass over the page, on its own layer: a backdrop filter on the header itself
          would make it the box the full-screen mobile menu (position: fixed) is sized to. */}
      <div aria-hidden="true" className="absolute inset-0 -z-10 bg-ink/80 backdrop-blur-lg" />
      {/* Three columns from md up, so the menu pill stays centred whatever the sides hold. */}
      <Container className="flex h-16 items-center justify-between md:grid md:grid-cols-[1fr_auto_1fr]">
        {/* 44 px tall on touch screens: the text alone is a 32 px target. */}
        <Link href="/" className="relative z-20 inline-flex items-center justify-self-start font-display text-2xl pointer-coarse:min-h-11">
          {SITE.name}
          <span className="text-accent">.</span>
        </Link>
        <nav aria-label="Main" className="hidden md:block">
          {/* The current section is filled in the text colour: a shape as well as a colour. */}
          <NavLinks
            className="flex items-center gap-1 rounded-btn border border-line bg-ink-raised p-1 text-sm font-medium"
            linkClassName="block rounded-btn px-4 py-1.5 transition-colors duration-200"
            idleClassName="text-muted hover:bg-paper/10 hover:text-paper"
            currentClassName="bg-paper text-ink"
          />
        </nav>
        <p className="hidden items-center gap-2.5 justify-self-end text-sm font-medium lg:flex">
          <span aria-hidden="true" className="status-dot relative size-2 rounded-full bg-accent" />
          {SITE.status}
        </p>
        <MobileNav />
      </Container>
    </header>
  );
}
