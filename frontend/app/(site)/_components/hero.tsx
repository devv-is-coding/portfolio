import { getImageProps } from "next/image";
import { preload } from "react-dom";
import { ColorBends } from "@/components/color-bends";
import { ButtonLink } from "@/components/ui/button-link";
import { Container } from "@/components/ui/container";
import { Eyebrow } from "@/components/ui/eyebrow";
import { Marquee } from "@/components/ui/marquee";
import { SITE } from "@/lib/site";
import portrait from "@/public/images/portrait.png";

const MARQUEE_WORDS = ["Plan", "Design", "Develop", "Test", "Deploy", "Repeat"] as const;
// The accent with a darker band for depth, read from the design tokens: no color outside the palette.
const BAND_COLORS = ["--color-accent", "--color-line"] as const;

const PORTRAIT_ALT = `Portrait of ${SITE.name}`;

// The portrait is the phone LCP: loaded at once, at high priority. getImageProps() gives the
// optimized srcset (AVIF) without next/image's browser JavaScript.
const { props: portraitProps } = getImageProps({
  src: portrait,
  alt: PORTRAIT_ALT,
  loading: "eager",
  fetchPriority: "high",
  // Below lg its width follows the height left for it, up to the file's own 372 px.
  sizes: "(min-width: 1280px) 460px, (min-width: 1024px) 340px, 372px",
});

/** The home page's first screen: headline, calls to action and the portrait. */
export function Hero() {
  // What next/image's `preload` does: a <link rel="preload"> in <head>, so the browser asks
  // for the portrait before it reaches the <img> (it was requested ~0.9 s late without it).
  preload(portraitProps.src, {
    as: "image",
    imageSrcSet: portraitProps.srcSet,
    imageSizes: portraitProps.sizes,
    fetchPriority: "high",
  });
  return (
    // One screen below the header (h-16 + its 1px border), so the marquee is the first screen's
    // bottom edge; taller only when the content can't fit (min-h-fit: very short screens).
    <section className="relative isolate flex h-[calc(100svh-4rem-1px)] min-h-fit flex-col overflow-x-clip">
      {/* Behind the content (isolate + -z-10), dimmed and softened so it never competes with the headline. */}
      <div aria-hidden="true" className="absolute inset-0 -z-10 opacity-25 blur-lg">
        <ColorBends colors={BAND_COLORS} intensity={1} noise={0.08} />
      </div>
      {/* Phones and tablets: text, then the photo in whatever height is left (at least 11rem).
          Desktop: text centered beside the photo. */}
      <Container className="grid flex-1 grid-rows-[auto_minmax(11rem,1fr)] gap-6 pt-8 sm:gap-8 sm:pt-10 lg:grid-cols-[1fr_auto] lg:grid-rows-[auto] lg:gap-12">
        {/* A size container: the headline's size follows this column's width (cqi). While the
            hero scrolls away the text drifts up faster and fades (lib/motion parallax). */}
        <div
          data-motion="parallax"
          data-motion-y="-25"
          data-motion-fade
          className="@container flex flex-col gap-5 sm:gap-7 lg:self-center lg:pb-10"
        >
          <Eyebrow>Full-stack developer</Eyebrow>
          <h1 className="font-display text-display font-extrabold uppercase">
            {/* Two lines from sm up; on phones one word per line, so the size can stay big. */}
            <span className="block animate-rise">
              Building <span className="max-sm:block">systems</span>
            </span>
            <span className="block animate-rise text-accent [animation-delay:120ms]">
              Creating <span className="max-sm:block">solutions</span>
            </span>
          </h1>
          <p className="max-w-2xl leading-[1.7] text-muted sm:text-xl">
            I engineer APIs, architect backend systems, and build web applications that solve
            real-world problems. Focused on clean code, thoughtful architecture, and meaningful
            solutions.
          </p>
          <div className="flex flex-wrap gap-3">
            <ButtonLink href="/projects">See the work</ButtonLink>
            <ButtonLink href="/contact" variant="outline">
              Get in touch
            </ButtonLink>
          </div>
        </div>
        {/* The photo's bottom edge sits on the marquee, so its crop at the waist never shows.
            Below lg it is as tall as the row left for it (never above its own 574 px): h-0 +
            min-h-full fills the row without making it taller. From lg its width follows the screen
            height (64svh - 120px) so it fills the hero top to bottom and everything fits one
            screen; on xl up to 460 px (1.24x the file, slightly soft but never distorted). */}
        <div className="flex h-0 min-h-full items-end justify-center lg:block lg:h-auto lg:min-h-0 lg:self-end">
          {/* While the hero scrolls away the portrait sinks slower than the page, behind the marquee. */}
          <div
            data-motion="parallax"
            data-motion-y="14"
            className="relative aspect-[372/574] h-full max-h-[574px] max-w-full lg:h-auto lg:max-h-none lg:w-[clamp(260px,calc(64svh-120px),340px)] xl:w-[clamp(260px,calc(64svh-120px),460px)]"
          >
            <div
              aria-hidden="true"
              className="absolute inset-x-[-8%] top-[12%] bottom-0 rounded-t-full border border-line bg-ink-raised"
            />
            <picture className="contents">
              <img {...portraitProps} alt={PORTRAIT_ALT} className="relative size-full animate-rise [animation-delay:120ms]" />
            </picture>
          </div>
        </div>
      </Container>
      <Marquee items={MARQUEE_WORDS} />
    </section>
  );
}
