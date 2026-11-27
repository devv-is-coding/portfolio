import type { ReactNode } from "react";
import { Container } from "@/components/ui/container";
import { cn } from "@/lib/cn";

/*
 * Loading placeholders shaped like the content they stand in for, used as Suspense fallbacks
 * on the public pages. Server-rendered, CSS only (the pulse stops with reduced motion, see
 * globals.css). Each keeps its content's size, so nothing jumps when the data arrives.
 */

/** One placeholder shape. */
function Bone({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-md bg-line/60", className)} />;
}

/**
 * Wraps a skeleton: announced once to screen readers, the shapes themselves hidden.
 * `className` lays out the shapes (it's on the element that holds them).
 */
function Loading({ label, className, children }: { label: string; className?: string; children: ReactNode }) {
  return (
    <div role="status">
      <span className="sr-only">{label}</span>
      <div aria-hidden="true" className={className}>
        {children}
      </div>
    </div>
  );
}

function HeadingSkeleton() {
  return (
    <div className="flex flex-col gap-4">
      <Bone className="h-3 w-28" />
      <Bone className="h-[clamp(2.25rem,6vw,4.75rem)] w-3/5 max-w-xl" />
    </div>
  );
}

/** Like components/project-card.tsx: picture, title, summary, skills. */
function ProjectCardSkeleton() {
  return (
    <div className="flex flex-col overflow-hidden rounded-card border border-line bg-ink-raised">
      <Bone className="aspect-[16/10] rounded-none bg-ink" />
      <div className="flex flex-col gap-4 p-6">
        <Bone className="h-7 w-2/3" />
        <div className="flex flex-col gap-2">
          <Bone className="h-4 w-full" />
          <Bone className="h-4 w-4/5" />
        </div>
        <div className="flex gap-2">
          <Bone className="h-6 w-16 rounded-btn" />
          <Bone className="h-6 w-20 rounded-btn" />
          <Bone className="h-6 w-14 rounded-btn" />
        </div>
      </div>
    </div>
  );
}

/** Like components/post-row.tsx: date and category, title, excerpt. */
function PostRowSkeleton() {
  return (
    <div className="flex flex-col gap-3 border-t border-line py-8">
      <Bone className="h-3 w-44" />
      <Bone className="h-7 w-3/4 max-w-2xl" />
      <div className="flex max-w-2xl flex-col gap-2">
        <Bone className="h-4 w-full" />
        <Bone className="h-4 w-2/3" />
      </div>
    </div>
  );
}

/** Like components/timeline.tsx: period, title, place, a line of text. */
function TimelineRowSkeleton() {
  return (
    <div className="grid gap-3 border-t border-line py-8 md:grid-cols-[14rem_1fr] md:gap-10">
      <Bone className="h-3 w-32" />
      <div className="flex flex-col gap-2">
        <Bone className="h-7 w-1/2" />
        <Bone className="h-4 w-1/3" />
        <Bone className="mt-2 h-4 w-3/4 max-w-2xl" />
      </div>
    </div>
  );
}

function FilterTagsSkeleton() {
  return (
    <div className="flex flex-wrap gap-2">
      {["w-12", "w-16", "w-20", "w-14", "w-18"].map((width) => (
        <Bone key={width} className={cn("h-7 rounded-btn", width)} />
      ))}
    </div>
  );
}

/** The projects page list: filter tags and a grid of cards, at least a screen tall. */
export function ProjectListSkeleton() {
  return (
    <Loading label="Loading projects" className="flex min-h-svh flex-col gap-10">
      <FilterTagsSkeleton />
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }, (_, index) => (
          <ProjectCardSkeleton key={index} />
        ))}
      </div>
    </Loading>
  );
}

/** The blog page list: filter tags and rows of posts, at least a screen tall. */
export function PostListSkeleton() {
  return (
    <Loading label="Loading posts" className="flex min-h-svh flex-col gap-10">
      <FilterTagsSkeleton />
      <div>
        {Array.from({ length: 5 }, (_, index) => (
          <PostRowSkeleton key={index} />
        ))}
      </div>
    </Loading>
  );
}

/** The home page below the hero: its first section (the work stack's headline and first card), a screen tall. */
export function HomeSectionsSkeleton() {
  return (
    <Loading label="Loading" className="min-h-svh border-t border-line py-20 sm:py-28">
      <Container className="flex flex-col gap-12">
        <Bone className="h-[clamp(3rem,7.5vw,7.25rem)] w-[min(36rem,80%)]" />
        <Bone className="h-[26rem] rounded-card md:h-[min(72svh,40rem)]" />
      </Container>
    </Loading>
  );
}

/** The about page below its title: the profile, then the first timeline section. */
export function AboutSkeleton() {
  return (
    <Loading label="Loading the profile" className="min-h-svh">
      <Container className="flex flex-col gap-6 py-12 sm:py-16">
        <Bone className="h-9 w-72 max-w-full sm:h-10" />
        <Bone className="h-9 w-56 max-w-full sm:h-10" />
        <Bone className="h-3 w-40" />
        <div className="flex max-w-2xl flex-col gap-3">
          <Bone className="h-5 w-full" />
          <Bone className="h-5 w-full" />
          <Bone className="h-5 w-3/4" />
        </div>
        <div className="flex gap-3">
          <Bone className="h-12 w-32 rounded-btn" />
          <Bone className="h-12 w-36 rounded-btn" />
        </div>
      </Container>
      <div className="border-t border-line py-20 sm:py-28">
        <Container className="flex flex-col gap-10">
          <HeadingSkeleton />
          <div>
            {Array.from({ length: 3 }, (_, index) => (
              <TimelineRowSkeleton key={index} />
            ))}
          </div>
        </Container>
      </div>
    </Loading>
  );
}

/** A project or post page: back link, date, title, summary, picture, first paragraphs. */
export function ArticleSkeleton({ narrow = false }: { narrow?: boolean }) {
  return (
    <Loading label="Loading">
      <Container className={cn("flex flex-col gap-10 py-16 sm:py-24", narrow && "max-w-3xl")}>
        <Bone className="h-3 w-28" />
        <div className="flex flex-col gap-6">
          <Bone className="h-3 w-32" />
          <Bone className="h-[clamp(2.25rem,6vw,4.75rem)] w-4/5" />
          <div className="flex max-w-2xl flex-col gap-3">
            <Bone className="h-6 w-full" />
            <Bone className="h-6 w-2/3" />
          </div>
        </div>
        <Bone className="aspect-[16/9] w-full rounded-card" />
        <div className="flex max-w-3xl flex-col gap-3">
          <Bone className="h-5 w-full" />
          <Bone className="h-5 w-full" />
          <Bone className="h-5 w-5/6" />
        </div>
      </Container>
    </Loading>
  );
}
