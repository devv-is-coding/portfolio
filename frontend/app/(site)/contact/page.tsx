import type { Metadata } from "next";
import { Suspense } from "react";
import { PosterHeading } from "@/components/poster-heading";
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
    <Container className="flex flex-col gap-12 py-16 sm:py-24">
      <div className="flex flex-col gap-6">
        <PosterHeading as="h1" title="Get in touch" />
        <p className="max-w-2xl text-lg leading-relaxed text-muted">
          {SITE.availability} Tell me about the role, the project or your question.
        </p>
      </div>
      <div className="grid gap-16 lg:grid-cols-[minmax(0,7fr)_minmax(0,4fr)] lg:gap-20">
        <div className="relative">
          <ContactForm />
        </div>
        <Suspense>
          <ContactDetails />
        </Suspense>
      </div>
    </Container>
  );
}

/** Other ways to reach me, from the profile, as a large list; nothing without a profile. */
async function ContactDetails() {
  await readAtRequestTimeWithoutApi();
  const profile = await getProfile();
  if (!profile || (!profile.email && profile.social_links.length === 0)) {
    return null;
  }
  const links = [
    ...(profile.email ? [{ label: "Email", detail: profile.email, href: `mailto:${profile.email}`, external: false }] : []),
    ...profile.social_links.map((link) => ({ label: platformName(link.platform), detail: null, href: link.url, external: true })),
  ];
  return (
    <aside className="flex flex-col gap-4">
      <h2 className="text-sm font-semibold text-muted">Elsewhere</h2>
      <ul className="border-t border-line">
        {links.map((link) => (
          <li key={link.href} className="border-b border-line">
            <a
              href={link.href}
              {...(link.external ? { target: "_blank", rel: "noopener noreferrer me" } : {})}
              className="group flex items-center justify-between gap-4 py-5 transition-colors hover:text-accent"
            >
              <span className="flex min-w-0 flex-col">
                <span className="font-display text-[clamp(1.75rem,2.6vw,2.5rem)] leading-none tracking-[-0.02em]">
                  {link.label}
                </span>
                {link.detail && <span className="mt-2 truncate text-sm text-muted">{link.detail}</span>}
              </span>
              <span
                aria-hidden="true"
                className="shrink-0 text-2xl transition-transform duration-300 ease-(--ease-ui) group-hover:translate-x-1 group-hover:-translate-y-1"
              >
                ↗
              </span>
            </a>
          </li>
        ))}
      </ul>
    </aside>
  );
}
