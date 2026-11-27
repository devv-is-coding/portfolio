import type { Metadata } from "next";
import { Suspense } from "react";
import { PosterHeading } from "@/components/poster-heading";
import { AboutSkeleton } from "@/components/skeletons";
import { Container } from "@/components/ui/container";
import { SITE } from "@/lib/site";
import { SkillsOverview } from "@/app/(site)/_components/home-sections";
import {
  CertificationsSection,
  EducationSection,
  ExperienceSection,
  ProfileIntro,
} from "./_components/about-sections";

export const metadata: Metadata = {
  title: "About",
  description: `Who ${SITE.name} is: experience, education, certifications and skills.`,
  alternates: { canonical: "/about" },
};

export default function AboutPage() {
  return (
    <>
      <Container className="pt-16 sm:pt-24">
        <PosterHeading as="h1" title="About me" />
      </Container>
      {/*
        One boundary for everything below the title, at least a screen tall, fallback and
        content alike: when the page renders per request, the sections stream in without
        pushing each other (or the footer) around. Measured: CLS 0.43 with one per section.
      */}
      <Suspense fallback={<AboutSkeleton />}>
        <div className="min-h-svh">
          <Container className="py-12 sm:py-16">
            <ProfileIntro />
          </Container>
          <ExperienceSection />
          <EducationSection />
          <CertificationsSection />
          <SkillsOverview />
        </div>
      </Suspense>
    </>
  );
}
