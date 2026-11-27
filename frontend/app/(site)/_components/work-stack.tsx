import Link from "next/link";
import type { CSSProperties } from "react";
import { MediaImage } from "@/components/media-image";
import { PosterHeading } from "@/components/poster-heading";
import { Container } from "@/components/ui/container";
import { TextLink } from "@/components/ui/text-link";
import { getProjects, type ProjectSummary, readAtRequestTimeWithoutApi } from "@/lib/api/public";
import { cn } from "@/lib/cn";
import { formatWorkPeriod } from "@/lib/format";

// Featured projects on the home page; without any featured, the newest ones.
const MAX_FEATURED = 6;
const MAX_NEWEST = 3;
const MAX_SKILLS = 4;

// The cards take turns: gold, cream, the raised surface. Text on the light ones is ink, and
// so is their focus ring (on-accent): the gold ring vanished on them.
const TONES = [
  { card: "on-accent bg-accent text-accent-ink", soft: "text-accent-ink/75" },
  { card: "on-accent bg-cream text-ink", soft: "text-cream-muted" },
  { card: "border border-line bg-ink-raised text-paper", soft: "text-muted" },
] as const;

/**
 * The featured projects as big cards that stack into a deck as the page scrolls, on every
 * screen: each sticks under the header a strip lower than the one before, and the next slides
 * over it (CSS sticky, no script). Left out when there are no published projects.
 */
export async function WorkStack() {
  await readAtRequestTimeWithoutApi();
  const featured = await getProjects({ featured: true, size: MAX_FEATURED });
  const projects =
    featured.items.length > 0 ? featured.items : (await getProjects({ size: MAX_NEWEST })).items;
  if (projects.length === 0) {
    return null;
  }
  return (
    <section className="below-fold border-t border-line py-20 sm:py-28">
      <Container className="flex flex-col gap-12">
        <PosterHeading
          title="Selected work"
          count={projects.length}
          action={<TextLink href="/projects">See all projects</TextLink>}
        />
        {/* work-stack (globals.css) sizes the deck from the number of cards (--n). */}
        <ol style={{ "--n": projects.length } as CSSProperties} className="work-stack flex flex-col gap-6 md:gap-8">
          {projects.map((project, index) => (
            <WorkCard key={project.id} project={project} index={index} />
          ))}
          {/* Room for the finished deck to stay put a while before the page moves on: a sticky
              card only stays stuck while its list goes on below it. */}
          <li aria-hidden="true" className="h-[30svh]" />
        </ol>
      </Container>
    </section>
  );
}

/**
 * A project without a screenshot shows what it was built with instead (the title again read
 * as a placeholder): every tool and where it can be seen, as a spec sheet on a panel a step
 * darker than the card (the period is already under the title). Each row only with its data;
 * nothing at all without either.
 */
function ProjectFacts({ project }: { project: ProjectSummary }) {
  const places = [project.live_url && "Live site", project.repository_url && "Source code"].filter(Boolean);
  const rows = [
    { label: "Built with", value: project.skills.map((skill) => skill.name).join(", "), large: true },
    { label: "Links", value: places.join(" · "), large: false },
  ].filter((row) => row.value);
  if (rows.length === 0) {
    return null;
  }
  return (
    <dl className="flex aspect-[16/10] flex-col justify-center gap-6 bg-current/8 p-6 sm:p-10 md:max-h-[calc(var(--card-h)-4rem)]">
      {rows.map((row) => (
        <div key={row.label} className="flex flex-col gap-1.5 border-t border-current/25 pt-3">
          <dt className="text-sm font-semibold opacity-75">{row.label}</dt>
          <dd className={row.large ? "font-display text-[clamp(1.75rem,3vw,2.75rem)] leading-[0.95]" : "font-semibold"}>
            {row.value}
          </dd>
        </div>
      ))}
    </dl>
  );
}

function WorkCard({ project, index }: { project: ProjectSummary; index: number }) {
  const tone = TONES[index % TONES.length];
  const period = formatWorkPeriod(project.started_on, project.ended_on);
  const { thumbnail } = project;
  return (
    // Sticks one peek lower than the card before it, so the deck keeps every earlier card's
    // top showing as a strip (globals.css: --peek, --card-h).
    // The top padding equals the peek (2.5rem, 3rem from md), so a strip never cuts text.
    <li style={{ "--i": index } as CSSProperties} className="sticky top-[calc(var(--deck-top)+var(--i)*var(--peek))]">
      <article
        className={cn(
          "group relative grid min-h-(--card-h) gap-6 rounded-card px-6 pt-10 pb-6 sm:px-8 sm:pb-8 md:grid-cols-[5fr_7fr] md:gap-8 md:px-10 md:pt-12 md:pb-10",
          tone.card,
        )}
      >
        <div data-reveal className="flex flex-col justify-between gap-6">
          <div className="flex flex-col gap-3">
            <h3 className="font-display text-[clamp(2.5rem,4.6vw,4.75rem)] leading-[0.9] tracking-[-0.03em]">
              {/* The whole card is the link (its box covers the card). */}
              <Link href={`/projects/${project.slug}`} className="after:absolute after:inset-0 after:rounded-card">
                {project.title}
              </Link>
            </h3>
            {period && <p className={cn("text-sm font-semibold", tone.soft)}>{period}</p>}
            {project.short_description && (
              <p className={cn("line-clamp-4 max-w-[40ch] leading-relaxed", tone.soft)}>
                {project.short_description}
              </p>
            )}
          </div>
          <div className="flex flex-col gap-5">
            {project.skills.length > 0 && (
              <ul className="flex flex-wrap gap-2" aria-label="Skills">
                {project.skills.slice(0, MAX_SKILLS).map((skill) => (
                  <li key={skill.id} className="rounded-btn border-[1.5px] border-current px-3.5 py-1 text-sm font-semibold">
                    {skill.name}
                  </li>
                ))}
              </ul>
            )}
            <span aria-hidden="true" className="inline-flex items-center gap-2 font-semibold">
              See the project
              <span className="transition-transform duration-300 ease-(--ease-ui) group-hover:translate-x-1.5">→</span>
            </span>
          </div>
        </div>
        <div
          data-reveal
          style={{ "--reveal": 1 } as CSSProperties}
          // A picture with rounded corners and a shadow, no border: a frame read as a card in a card.
          className="self-center overflow-hidden rounded-panel shadow-[0_30px_60px_-30px_rgb(14_14_16/0.5)]"
        >
          {thumbnail ? (
            <MediaImage
              src={thumbnail.url}
              alt={thumbnail.alt_text ?? ""}
              width={thumbnail.width}
              height={thumbnail.height}
              sizes="(min-width: 1280px) 42rem, (min-width: 768px) 56vw, 100vw"
              className="aspect-[16/10] w-full object-cover object-top transition-transform duration-700 ease-(--ease-enter) pointer-fine:group-hover:scale-[1.035] md:max-h-[calc(var(--card-h)-4rem)]"
            />
          ) : (
            <ProjectFacts project={project} />
          )}
        </div>
      </article>
    </li>
  );
}
