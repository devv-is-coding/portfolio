import Link from "next/link";
import { Suspense } from "react";
import { HiddenOn } from "@/components/hidden-on";
import { ProfileLinks } from "@/components/profile-links";
import { SectionErrorBoundary } from "@/components/section-error-boundary";
import { Container } from "@/components/ui/container";
import { SITE } from "@/lib/site";

// The main action, word for word as the hero's button (TODO.md Redesign).
const MAIN_ACTION = "Get in touch";

/** The close: the page ends on gold as the welcome began, with the main action set huge. */
// Its divider is part of it, so on /contact (no close) the footer starts without a stray line.
const close = (
  <div className="flex flex-col gap-6 border-b-[1.5px] border-accent-ink pt-16 pb-16 sm:pt-24">
    <p className="text-lg font-semibold">Have a role or a project in mind?</p>
    <Link
      href="/contact"
      className="group flex items-center justify-between gap-6 font-display text-[clamp(4rem,13vw,13rem)] leading-[0.86] tracking-[-0.035em]"
    >
      {MAIN_ACTION}
      {/* The circle is sized in the link's em (huge); the arrow inside is set smaller. */}
      <span
        aria-hidden="true"
        className="grid size-[0.62em] shrink-0 place-items-center rounded-full bg-accent-ink text-accent transition-transform duration-500 ease-(--ease-enter) group-hover:-rotate-45"
      >
        <span className="text-[0.34em] leading-none">→</span>
      </span>
    </Link>
  </div>
);

export function SiteFooter() {
  return (
    <footer className="on-accent rounded-t-[2.25rem] bg-accent text-accent-ink">
      <Container className="flex flex-col pb-10">
        {/* On the contact page itself the close would point at that page: left out. */}
        <Suspense fallback={close}>
          <HiddenOn path="/contact">{close}</HiddenOn>
        </Suspense>
        <div className="flex flex-col gap-6 pt-8 md:flex-row md:items-start md:justify-between">
          <p className="font-semibold">© {SITE.name} · Built with Next.js and FastAPI</p>
          {/* From the profile; nothing when the API has none or fails (the footer still shows). */}
          <SectionErrorBoundary fallback={null}>
            <Suspense fallback={null}>
              <ProfileLinks />
            </Suspense>
          </SectionErrorBoundary>
        </div>
      </Container>
    </footer>
  );
}
