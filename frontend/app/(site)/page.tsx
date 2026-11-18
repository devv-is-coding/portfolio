import { Suspense } from "react";
import { FeaturedProjects, LatestPosts, SkillsOverview } from "./_components/home-sections";
import { Hero } from "./_components/hero";

export default function HomePage() {
  return (
    <>
      <Hero />
      {/*
        Below the fold. One boundary with a screen-tall fallback: when the page renders per
        request the sections stream in together, and the footer never jumps into view first.
      */}
      <Suspense fallback={<div className="min-h-svh" />}>
        <FeaturedProjects />
        <SkillsOverview />
        <LatestPosts />
      </Suspense>
    </>
  );
}
