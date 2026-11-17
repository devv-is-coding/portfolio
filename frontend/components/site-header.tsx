import Link from "next/link";
import { MobileNav } from "@/components/mobile-nav";
import { Container } from "@/components/ui/container";
import { NAV_ITEMS, SITE } from "@/lib/site";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-ink">
      <Container className="flex h-16 items-center justify-between">
        <Link href="/" className="relative z-20 font-display text-2xl font-extrabold tracking-tight">
          {SITE.name}
          <span className="text-accent">.</span>
        </Link>
        <nav aria-label="Main" className="hidden md:block">
          <ul className="flex items-center gap-8 font-mono text-xs uppercase tracking-[0.2em]">
            {NAV_ITEMS.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="text-muted transition-colors duration-200 hover:text-accent"
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        <MobileNav />
      </Container>
    </header>
  );
}
