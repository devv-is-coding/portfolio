import { Suspense } from "react";
import { FeaturedProjects, LatestPosts, SkillsOverview } from "./_components/home-sections";
import { Hero } from "./_components/hero";

export default function HomePage() {
  return (
    <>
      <Hero />
      {/* Below the fold: each section streams in on its own if it isn't prerendered. */}
      <Suspense>
        <FeaturedProjects />
      </Suspense>
      <Suspense>
        <SkillsOverview />
      </Suspense>
      <Suspense>
        <LatestPosts />
      </Suspense>
    </>
  );
}
