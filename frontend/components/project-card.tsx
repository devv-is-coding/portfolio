import Link from "next/link";
import { MediaImage } from "@/components/media-image";
import { Tag } from "@/components/ui/tag";
import type { ProjectSummary } from "@/lib/api/public";

const MAX_SKILLS = 4;

/** A project in a grid: thumbnail, title, summary and its first skills; the whole card links. */
type ProjectCardProps = {
  project: ProjectSummary;
  sizes: string;
  /** `h2` where the cards sit right under the page title, `h3` inside a section. */
  headingLevel?: "h2" | "h3";
};

export function ProjectCard({ project, sizes, headingLevel: Heading = "h3" }: ProjectCardProps) {
  const { thumbnail } = project;
  return (
    <article className="group relative flex flex-col overflow-hidden rounded-2xl border border-line bg-ink-raised transition-colors hover:border-accent">
      <div className="aspect-[16/10] overflow-hidden bg-ink">
        {thumbnail ? (
          <MediaImage
            src={thumbnail.url}
            alt={thumbnail.alt_text ?? ""}
            width={thumbnail.width}
            height={thumbnail.height}
            sizes={sizes}
            className="size-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
        ) : (
          <div aria-hidden="true" className="flex size-full items-center justify-center font-display text-5xl font-extrabold text-line uppercase">
            {project.title.slice(0, 2)}
          </div>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-4 p-6">
        <Heading className="font-display text-2xl font-extrabold">
          <Link href={`/projects/${project.slug}`} className="after:absolute after:inset-0">
            {project.title}
          </Link>
        </Heading>
        {project.short_description && <p className="text-muted">{project.short_description}</p>}
        {project.skills.length > 0 && (
          <ul className="mt-auto flex flex-wrap gap-2" aria-label="Skills">
            {project.skills.slice(0, MAX_SKILLS).map((skill) => (
              <li key={skill.id}>
                <Tag>{skill.name}</Tag>
              </li>
            ))}
          </ul>
        )}
      </div>
    </article>
  );
}
