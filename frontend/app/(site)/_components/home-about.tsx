import { LitMarkdown } from "@/components/markdown";
import { PosterHeading } from "@/components/poster-heading";
import { Container } from "@/components/ui/container";
import { TextLink } from "@/components/ui/text-link";
import {
  getEducation,
  getExperiences,
  getProfile,
  readAtRequestTimeWithoutApi,
} from "@/lib/api/public";
import { formatPeriod } from "@/lib/format";

type Fact = { label: string; value: string };

/**
 * About, from the API: the biography in large type, its words lighting up as it scrolls
 * through (LitMarkdown), beside the facts the profile and the timeline hold (where he is,
 * the current role, the latest study) and the résumé. Each part only when it exists; the
 * section is left out without a profile. The full story is on /about.
 */
export async function HomeAbout() {
  await readAtRequestTimeWithoutApi();
  const [profile, experiences, education] = await Promise.all([getProfile(), getExperiences(), getEducation()]);
  if (!profile) {
    return null;
  }
  const current = experiences.find((entry) => entry.is_current);
  const study = education[0];
  const facts: Fact[] = [
    ...(profile.location ? [{ label: "Based in", value: profile.location }] : []),
    ...(current ? [{ label: "Now", value: `${current.position} at ${current.company}` }] : []),
    ...(study
      ? [{ label: "Studied", value: `${study.degree}, ${study.institution} (${formatPeriod(study.start_date, study.end_date)})` }]
      : []),
  ];
  return (
    <section className="below-fold border-t border-line py-20 sm:py-28">
      <Container className="flex flex-col gap-12">
        <PosterHeading title="About me" action={<TextLink href="/about">See the full story</TextLink>} />
        <div className="grid gap-12 lg:grid-cols-[minmax(0,7fr)_minmax(0,4fr)] lg:gap-16">
          {profile.biography ? (
            <LitMarkdown className="font-display text-[clamp(1.75rem,3.4vw,3rem)] leading-[1.08] tracking-[-0.02em]">
              {profile.biography}
            </LitMarkdown>
          ) : (
            // Without a biography the headline stands in, so the section still says who he is.
            profile.headline && (
              <p className="font-display text-[clamp(1.75rem,3.4vw,3rem)] leading-[1.08] tracking-[-0.02em]">
                {profile.full_name}, {profile.headline.toLowerCase()}.
              </p>
            )
          )}
          {(facts.length > 0 || profile.resume) && (
            <div className="flex flex-col gap-8 lg:pt-2">
              {facts.length > 0 && (
                <dl className="flex flex-col border-t border-line">
                  {facts.map((fact) => (
                    <div key={fact.label} className="flex flex-col gap-1 border-b border-line py-4">
                      <dt className="text-sm font-semibold text-muted">{fact.label}</dt>
                      <dd className="text-lg">{fact.value}</dd>
                    </div>
                  ))}
                </dl>
              )}
              {profile.resume && (
                <div>
                  <TextLink href={profile.resume.url} external>
                    Download the résumé
                  </TextLink>
                </div>
              )}
            </div>
          )}
        </div>
      </Container>
    </section>
  );
}
