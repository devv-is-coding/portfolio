import type { Metadata } from "next";
import { Suspense } from "react";
import { SectionErrorBoundary } from "@/components/section-error-boundary";
import { HomeSectionsSkeleton } from "@/components/skeletons";
import { Hero } from "./_components/hero";
import { HomeAbout } from "./_components/home-about";
import { SkillRows } from "./_components/skill-rows";
import { WorkStack } from "./_components/work-stack";
import { WritingRows } from "./_components/writing-rows";

export const metadata: Metadata = {
  alternates: { canonical: "/" },
};

export default function HomePage() {
  return (
    <>
      <Hero />
      {/*
        Below the fold. One boundary with a screen-tall fallback: when the page renders per
        request the sections stream in together, and the footer never jumps into view first.
      */}
      {/* The hero needs no data: if the API fails, only these sections show a notice. */}
      {/* below-fold: skipped (not laid out) until it nears the screen. The wrapper is in the
          first HTML, so it is skipped from the first layout; the sections stream in later, and
          on their own each was laid out once before being skipped (measured: ~100 ms of
          blocking time on a slow phone). */}
      <div className="below-fold">
        <SectionErrorBoundary>
          <Suspense fallback={<HomeSectionsSkeleton />}>
            <WorkStack />
            <SkillRows />
            <WritingRows />
            <HomeAbout />
          </Suspense>
        </SectionErrorBoundary>
      </div>
    </>
  );
}
