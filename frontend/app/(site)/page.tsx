import type { Metadata } from "next";
import { Suspense } from "react";
import { SectionErrorBoundary } from "@/components/section-error-boundary";
import { HomeSectionsSkeleton } from "@/components/skeletons";
import { FeaturedProjects, LatestPosts, SkillsOverview } from "./_components/home-sections";
import { Hero } from "./_components/hero";

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
      <SectionErrorBoundary>
        <Suspense fallback={<HomeSectionsSkeleton />}>
          <FeaturedProjects />
          <SkillsOverview core />
          <LatestPosts />
        </Suspense>
      </SectionErrorBoundary>
    </>
  );
}
