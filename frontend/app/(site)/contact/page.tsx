import type { Metadata } from "next";
import { Suspense } from "react";
import { SectionHeading } from "@/components/section-heading";
import { Container } from "@/components/ui/container";
import { getProfile, readAtRequestTimeWithoutApi } from "@/lib/api/public";
import { SITE } from "@/lib/site";
import { platformName } from "@/lib/social";
import { ContactForm } from "./_components/contact-form";

export const metadata: Metadata = {
  title: "Contact",
  description: `Get in touch with ${SITE.name}.`,
  alternates: { canonical: "/contact" },
};

export default function ContactPage() {
  return (
    <Container className="grid gap-16 py-16 sm:py-24 lg:grid-cols-[1fr_22rem]">
      <div className="relative flex flex-col gap-10">
        <SectionHeading as="h1" eyebrow="Contact" title="Let's talk" />
        <p className="max-w-xl text-lg text-muted">
          {SITE.availability} Tell me about the role, the project or your question, and I&apos;ll
          get back to you.
        </p>
        <ContactForm />
      </div>
      <Suspense>
        <ContactDetails />
      </Suspense>
    </Container>
  );
}

/** Other ways to reach me, from the profile; nothing when there's no profile yet. */
async function ContactDetails() {
  await readAtRequestTimeWithoutApi();
  const profile = await getProfile();
  if (!profile || (!profile.email && profile.social_links.length === 0)) {
    return null;
  }
  return (
    <aside className="flex flex-col gap-6 border-t border-line pt-8 lg:mt-40 lg:border-t-0 lg:border-l lg:pt-0 lg:pl-10">
      <h2 className="font-mono text-xs uppercase tracking-[0.2em] text-muted">Elsewhere</h2>
      <ul className="flex flex-col gap-3">
        {profile.email && (
          <li>
            <a href={`mailto:${profile.email}`} className="text-lg hover:text-accent">
              {profile.email}
            </a>
          </li>
        )}
        {profile.social_links.map((link) => (
          <li key={link.id}>
            <a href={link.url} target="_blank" rel="noopener noreferrer me" className="text-lg hover:text-accent">
              {platformName(link.platform)} ↗
            </a>
          </li>
        ))}
      </ul>
    </aside>
  );
}
