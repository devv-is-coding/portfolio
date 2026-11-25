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
      <Container className="flex h-16 items-center justify-between">
        <Link href="/" className="relative z-20 font-display text-2xl font-extrabold tracking-tight">
          {SITE.name}
          <span className="text-accent">.</span>
        </Link>
        <nav aria-label="Main" className="hidden md:block">
          {/* The current section is lit and underlined in the accent: color plus a mark. */}
          <NavLinks
            className="flex items-center gap-8 font-mono text-xs uppercase tracking-[0.2em]"
            linkClassName="underline-offset-[0.7em] transition-colors duration-200 hover:text-accent"
            idleClassName="text-muted"
            currentClassName="text-paper underline decoration-accent decoration-2"
          />
        </nav>
        <MobileNav />
      </Container>
      {/* How far down the page the visitor is: a line filled by the scroll itself (globals.css). */}
      <div aria-hidden="true" className="scroll-progress absolute inset-x-0 -bottom-px h-px bg-accent" />
    </header>
  );
}
