import type { Metadata } from "next";
import { Suspense } from "react";
import { Container } from "@/components/ui/container";
import { Eyebrow } from "@/components/ui/eyebrow";
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
};

export default function AboutPage() {
  return (
    <>
      <Container className="flex flex-col gap-12 py-16 sm:py-24">
        <div className="flex flex-col gap-6">
          <Eyebrow>About</Eyebrow>
          <h1 className="font-display text-display font-extrabold uppercase">About me</h1>
        </div>
        <Suspense fallback={<div className="h-64 animate-pulse rounded-2xl bg-ink-raised" />}>
          <ProfileIntro />
        </Suspense>
      </Container>
      <Suspense>
        <ExperienceSection />
      </Suspense>
      <Suspense>
        <EducationSection />
      </Suspense>
      <Suspense>
        <CertificationsSection />
      </Suspense>
      <Suspense>
        <SkillsOverview />
      </Suspense>
    </>
  );
}
