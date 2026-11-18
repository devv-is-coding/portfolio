import Link from "next/link";
import { Container } from "@/components/ui/container";
import { SITE } from "@/lib/site";

export function SiteFooter() {
  return (
    <footer className="border-t border-line">
      <Container className="flex flex-col gap-10 py-16">
        <Link
          href="/contact"
          className="group font-display text-headline font-extrabold uppercase transition-colors duration-200 hover:text-accent"
        >
          Let&apos;s build something
          <span
            aria-hidden="true"
            className="ml-3 inline-block text-accent transition-transform duration-300 group-hover:translate-x-2"
          >
            →
          </span>
        </Link>
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted">
          © {SITE.name} · Built with Next.js and FastAPI
        </p>
      </Container>
    </footer>
  );
}
