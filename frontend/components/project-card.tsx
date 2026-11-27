import Link from "next/link";
import { MediaImage } from "@/components/media-image";
import type { ProjectSummary } from "@/lib/api/public";
import { formatWorkPeriod } from "@/lib/format";

const MAX_SKILLS = 4;

/** A project in a grid: picture, period, title, summary and its first skills; the whole card links. */
type ProjectCardProps = {
  project: ProjectSummary;
  sizes: string;
  /** `h2` where the cards sit right under the page title, `h3` inside a section. */
  headingLevel?: "h2" | "h3";
  /** On screen when the page opens: the picture loads at once, at high priority (not lazily). */
  priority?: boolean;
};

export function ProjectCard({ project, sizes, headingLevel: Heading = "h3", priority = false }: ProjectCardProps) {
  const { thumbnail } = project;
  const period = formatWorkPeriod(project.started_on, project.ended_on);
  return (
    <article className="group relative flex flex-col gap-5">
      <div className="aspect-[16/10] overflow-hidden rounded-card border border-line bg-ink-raised">
        {thumbnail ? (
          <MediaImage
            src={thumbnail.url}
            alt={thumbnail.alt_text ?? ""}
            width={thumbnail.width}
            height={thumbnail.height}
            sizes={sizes}
            loading={priority ? "eager" : "lazy"}
            fetchPriority={priority ? "high" : undefined}
            className="size-full object-cover object-top transition-transform duration-700 ease-(--ease-enter) pointer-fine:group-hover:scale-[1.035]"
          />
        ) : (
          // No screenshot yet: the title, set large on the card's surface.
          <div aria-hidden="true" className="flex size-full items-center justify-center p-6 text-center">
            <span className="font-display text-[clamp(2rem,4vw,3rem)] leading-[0.9] text-muted">{project.title}</span>
          </div>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-3">
        {period && <p className="text-sm font-semibold text-muted">{period}</p>}
        <Heading className="font-display text-[clamp(1.75rem,2.6vw,2.5rem)] leading-[0.95] tracking-[-0.02em] transition-colors group-hover:text-accent">
          <Link href={`/projects/${project.slug}`} className="after:absolute after:inset-0">
            {project.title}
          </Link>
        </Heading>
        {/* Three lines at most, so cards in a row stay even; the project page has the rest. */}
        {project.short_description && <p className="line-clamp-3 leading-relaxed text-muted">{project.short_description}</p>}
        {project.skills.length > 0 && (
          <ul className="mt-auto flex flex-wrap gap-2 pt-2" aria-label="Skills">
            {project.skills.slice(0, MAX_SKILLS).map((skill) => (
              <li key={skill.id} className="rounded-btn border border-line px-3 py-1 text-sm font-medium text-muted">
                {skill.name}
              </li>
            ))}
          </ul>
        )}
      </div>
    </article>
  );
}
