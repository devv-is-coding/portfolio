import { CertificateViewer } from "@/app/(site)/about/_components/certificate-viewer";
import { Markdown } from "@/components/markdown";
import { MediaImage } from "@/components/media-image";
import { SectionHeading } from "@/components/section-heading";
import { Timeline } from "@/components/timeline";
import { ButtonLink } from "@/components/ui/button-link";
import { Container } from "@/components/ui/container";
import { Tag } from "@/components/ui/tag";
import {
  getCertifications,
  getEducation,
  getExperiences,
  getProfile,
  readAtRequestTimeWithoutApi,
} from "@/lib/api/public";
import { formatMonthYear, formatPeriod } from "@/lib/format";
import { platformName } from "@/lib/social";

const SECTION = "border-t border-line py-20 sm:py-28";

/** Name, headline, biography, avatar and the ways to get in touch. */
export async function ProfileIntro() {
  await readAtRequestTimeWithoutApi();
  const profile = await getProfile();
  if (!profile) {
    return <p className="text-lg text-muted">The full profile is on its way.</p>;
  }
  const { avatar, resume } = profile;
  return (
    <div className="grid gap-12 lg:grid-cols-[1fr_20rem]">
      <div className="flex flex-col gap-6">
        <p className="font-display text-3xl font-extrabold sm:text-4xl">
          {profile.full_name}
          {profile.headline && <span className="block text-accent">{profile.headline}</span>}
        </p>
        {profile.location && <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted">{profile.location}</p>}
        {profile.biography && <Markdown className="max-w-2xl text-lg">{profile.biography}</Markdown>}
        <div className="flex flex-wrap gap-3">
          {profile.email && (
            <ButtonLink href={`mailto:${profile.email}`}>Email me</ButtonLink>
          )}
          {resume && (
            <ButtonLink href={resume.url} variant="outline" target="_blank" rel="noopener noreferrer">
              Résumé (PDF)
            </ButtonLink>
          )}
        </div>
        {profile.social_links.length > 0 && (
          <ul className="flex flex-wrap gap-x-6 gap-y-2" aria-label="Elsewhere">
            {profile.social_links.map((link) => (
              <li key={link.id}>
                <a
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer me"
                  className="font-mono text-xs uppercase tracking-[0.2em] text-muted transition-colors hover:text-accent"
                >
                  {platformName(link.platform)} ↗
                </a>
              </li>
            ))}
          </ul>
        )}
      </div>
      {avatar && (
        // Uncovers as it scrolls into view (lib/motion "image").
        <div data-motion="image" className="h-fit overflow-hidden rounded-2xl border border-line">
          <MediaImage
            src={avatar.url}
            alt={avatar.alt_text ?? `Portrait of ${profile.full_name}`}
            width={avatar.width}
            height={avatar.height}
            sizes="(min-width: 1024px) 320px, 100vw"
            className="block h-auto w-full"
          />
        </div>
      )}
    </div>
  );
}

export async function ExperienceSection() {
  await readAtRequestTimeWithoutApi();
  const experiences = await getExperiences();
  if (experiences.length === 0) {
    return null;
  }
  return (
    <section className={SECTION}>
      <Container className="flex flex-col gap-10">
        <SectionHeading eyebrow="Career" title="Experience" />
        <Timeline
          entries={experiences.map((job) => ({
            id: job.id,
            period: formatPeriod(job.start_date, job.end_date),
            title: job.position,
            subtitle: [job.company, job.employment_type, job.location].filter(Boolean).join(" · "),
            description: job.description,
            badge: job.is_current ? <Tag className="border-accent text-accent">Current</Tag> : undefined,
          }))}
        />
      </Container>
    </section>
  );
}

export async function EducationSection() {
  await readAtRequestTimeWithoutApi();
  const education = await getEducation();
  if (education.length === 0) {
    return null;
  }
  return (
    <section className={SECTION}>
      <Container className="flex flex-col gap-10">
        <SectionHeading eyebrow="Study" title="Education" />
        <Timeline
          entries={education.map((school) => ({
            id: school.id,
            period: formatPeriod(school.start_date, school.end_date, "In progress"),
            title: [school.degree, school.field_of_study].filter(Boolean).join(", ") || school.institution,
            subtitle: school.institution,
            description: school.description,
          }))}
        />
      </Container>
    </section>
  );
}

export async function CertificationsSection() {
  await readAtRequestTimeWithoutApi();
  const certifications = await getCertifications();
  if (certifications.length === 0) {
    return null;
  }
  return (
    <section className={SECTION}>
      <Container className="flex flex-col gap-10">
        <SectionHeading eyebrow="Proof" title="Certifications" />
        <Timeline
          entries={certifications.map((certificate) => ({
            id: certificate.id,
            period: certificate.issued_at ? formatMonthYear(certificate.issued_at) : "",
            title: certificate.name,
            subtitle: [
              certificate.issuing_organization,
              certificate.expires_at &&
                `${certificate.is_expired ? "Expired" : "Valid until"} ${formatMonthYear(certificate.expires_at)}`,
            ]
              .filter(Boolean)
              .join(" · "),
            badge: certificate.is_expired ? <Tag className="border-signal text-signal">Expired</Tag> : undefined,
            link: certificate.credential_url
              ? { href: certificate.credential_url, label: "Show credential ↗" }
              : undefined,
            actions: certificate.image ? (
              <CertificateViewer title={certificate.name}>
                <MediaImage
                  src={certificate.image.url}
                  alt={certificate.image.alt_text ?? `${certificate.name} certificate`}
                  width={certificate.image.width}
                  height={certificate.image.height}
                  sizes="(min-width: 1200px) 1100px, 100vw"
                  loading="lazy"
                  className="mx-auto h-auto max-h-[78svh] w-auto max-w-full rounded-lg bg-ink-raised object-contain"
                />
              </CertificateViewer>
            ) : undefined,
          }))}
        />
      </Container>
    </section>
  );
}
