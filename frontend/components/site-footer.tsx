import Link from "next/link";
import { Container } from "@/components/ui/container";
import { SplitWords } from "@/components/ui/split-words";
import { SITE } from "@/lib/site";

const CALL_TO_ACTION = "Let's build something";

export function SiteFooter() {
  return (
    <footer className="border-t border-line">
      <Container className="flex flex-col gap-10 py-16">
        {/* The words slide up into view as the footer arrives (lib/motion). */}
        <Link
          href="/contact"
          aria-label={CALL_TO_ACTION}
          data-motion="words"
          className="group font-display text-headline font-extrabold uppercase transition-colors duration-200 hover:text-accent"
        >
          <SplitWords text={CALL_TO_ACTION} />
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
