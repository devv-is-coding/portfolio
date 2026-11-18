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
      <Container className="flex flex-col gap-6 pt-16 sm:pt-24">
        <Eyebrow>About</Eyebrow>
        <h1 className="font-display text-display font-extrabold uppercase">About me</h1>
      </Container>
      {/*
        One boundary for everything below the title, at least a screen tall, fallback and
        content alike: when the page renders per request, the sections stream in without
        pushing each other (or the footer) around. Measured: CLS 0.43 with one per section.
      */}
      <Suspense fallback={<div className="min-h-svh" />}>
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
