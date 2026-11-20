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
  sizes: "(min-width: 1280px) 370px, (min-width: 1024px) 340px, min(70vw, 300px)",
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
    <section className="relative isolate overflow-x-clip">
      {/* Behind the content (isolate + -z-10), dimmed and softened so it never competes with the headline. */}
      <div aria-hidden="true" className="absolute inset-0 -z-10 opacity-25 blur-lg">
        <ColorBends colors={BAND_COLORS} intensity={1} noise={0.08} />
      </div>
      {/* As tall as its content: the text block and the photo end up about the same height. */}
      <Container className="grid gap-12 pt-16 sm:pt-20 lg:grid-cols-[1fr_auto]">
        {/* A size container: the headline's size follows this column's width (cqi). */}
        <div className="@container flex flex-col gap-10 lg:pb-12">
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
          <p className="max-w-2xl text-lg leading-[1.7] text-muted sm:text-xl">
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
        {/* Bottom edge sits on the marquee, so the photo's crop at the waist never shows. */}
        <div className="relative mx-auto w-[min(70vw,300px)] self-end lg:mx-0 lg:w-[340px] xl:w-[370px]">
          <div
            aria-hidden="true"
            className="absolute inset-x-[-8%] top-[12%] bottom-0 rounded-t-full border border-line bg-ink-raised"
          />
          <picture className="contents">
            <img {...portraitProps} alt={PORTRAIT_ALT} className="relative h-auto w-full animate-rise [animation-delay:120ms]" />
          </picture>
        </div>
      </Container>
      <Marquee items={MARQUEE_WORDS} />
    </section>
  );
}
