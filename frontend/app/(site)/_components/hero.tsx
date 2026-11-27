import { getImageProps } from "next/image";
import { type CSSProperties, Fragment, Suspense } from "react";
import { ResumeBadge } from "@/app/(site)/_components/hero-badge";
import { HeroFacts } from "@/app/(site)/_components/hero-facts";
import { SectionErrorBoundary } from "@/components/section-error-boundary";
import { ButtonLink } from "@/components/ui/button-link";
import { Container } from "@/components/ui/container";
import { Eyebrow } from "@/components/ui/eyebrow";
import { SITE } from "@/lib/site";
import portrait from "@/public/images/portrait.webp";

const PORTRAIT_ALT = `Portrait of ${SITE.name}`;

// The headline in four poster lines; one word in the accent.
const HEADLINE = [
  { text: "Building", accent: false },
  { text: "systems,", accent: false },
  { text: "creating", accent: true },
  { text: "solutions.", accent: false },
];

// The portrait is a likely LCP: loaded at once, at high priority. getImageProps() gives the
// optimized srcset (AVIF) without next/image's browser JavaScript.
const { props: portraitProps } = getImageProps({
  src: portrait,
  alt: PORTRAIT_ALT,
  loading: "eager",
  fetchPriority: "high",
  // 110% of the block's height, its own width: about 500 px wide at 1440x900, 330 px on phones.
  sizes: "(min-width: 768px) 600px, 340px",
});

/**
 * The home page's first screen: the headline, the line under it and two actions; the portrait
 * (seated, in the graduation gown) standing in a cream block, its head above the block's edge; the facts row as the floor.
 * Nothing above the floor needs data, so it shows while the API wakes up; the facts and the
 * résumé link stream in. The welcome screen (components/intro.tsx) shrinks into the block.
 */
export function Hero() {
  return (
    // One screen below the header (h-16 + its 1px border) from md up; taller only when the
    // content can't fit (min-h-fit). Phones scroll.
    // overflow-x-clip: the portrait (110% of the block's height, its own width) never pushes the page sideways.
    <section className="hero flex flex-col overflow-x-clip md:h-[calc(100svh-4rem-1px)] md:min-h-fit">
      <Container className="grid flex-1 gap-10 py-8 md:grid-cols-2 md:gap-10 md:pb-6 lg:gap-14">
        {/* One group, centred in the column: on a tall screen the line and the buttons stay
            with the headline instead of dropping to the column's foot. */}
        <div className="flex flex-col justify-center gap-8 lg:gap-10">
          {/* The headline's size follows this column's width (--text-display, globals.css). */}
          <div className="flex flex-col gap-5">
            <Eyebrow className="hero-fade">Full-stack developer</Eyebrow>
            <h1 className="font-display text-display">
              {/* A real space between the lines: block boxes alone leave the text glued together
                  for search engines and some screen readers ("Buildingsystems,"). */}
              {HEADLINE.map((line, index) => (
                <Fragment key={line.text}>
                  {index > 0 && " "}
                  <span className="hero-mask block">
                    <span
                      className={line.accent ? "hero-line block text-accent" : "hero-line block"}
                      style={{ "--line": index } as CSSProperties}
                    >
                      {line.text}
                    </span>
                  </span>
                </Fragment>
              ))}
            </h1>
          </div>
          <div className="hero-fade flex flex-col gap-6">
            <p className="max-w-xl leading-relaxed text-muted xl:text-lg">
              I build web products end to end, from APIs and databases to the pages people use, from
              the Philippines. {SITE.availability}
            </p>
            <div className="flex flex-wrap gap-3">
              <ButtonLink href="/projects">See the work</ButtonLink>
              <ButtonLink href="/contact" variant="secondary">
                Get in touch
              </ButtonLink>
            </div>
          </div>
        </div>
        {/* The cream block. It starts a step below the column's top, and the portrait (110% of
            its height) stands on its floor, so the head rises above the edge and stays clear of
            the header. Clipped at its sides and floor (keeping the block's rounded corners) but
            not above, so the rising portrait never shows below it and the head stays free. On a
            portrait screen from md up (a tablet held upright) it sits at the column's foot at
            1.25 times its width: the column's full height would blow the portrait up and cut
            the sleeves. data-intro-target: the welcome screen shrinks into this box. */}
        <div
          data-intro-target
          className="hero-block relative mt-14 min-h-[26rem] rounded-card bg-cream [clip-path:inset(-100%_0_0_0_round_0_0_var(--radius-card)_var(--radius-card))] md:mt-16 md:min-h-0 md:portrait:aspect-[0.8] md:portrait:self-end"
        >
          <picture className="contents">
            <img
              {...portraitProps}
              alt={PORTRAIT_ALT}
              className="hero-portrait absolute bottom-0 left-1/2 h-[110%] w-auto max-w-none -translate-x-1/2"
            />
          </picture>
          {/* The résumé badge streams in from the profile; nothing until then, or without one. */}
          <SectionErrorBoundary fallback={null}>
            <Suspense fallback={null}>
              <ResumeBadge />
            </Suspense>
          </SectionErrorBoundary>
        </div>
      </Container>
      {/* The floor: facts from the API. A fixed height (two rows on phones), so the facts
          streaming in never move anything; if the API fails or has nothing, it stays empty. */}
      <div className="border-t border-line">
        <Container className="hero-fade h-36 md:h-20">
          <SectionErrorBoundary fallback={null}>
            <Suspense fallback={null}>
              <HeroFacts />
            </Suspense>
          </SectionErrorBoundary>
        </Container>
      </div>
    </section>
  );
}
