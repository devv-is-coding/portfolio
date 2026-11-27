import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { type CSSProperties, Suspense } from "react";
import { Markdown } from "@/components/markdown";
import { MediaImage } from "@/components/media-image";
import { ArticleSkeleton } from "@/components/skeletons";
import { ButtonLink } from "@/components/ui/button-link";
import { Container } from "@/components/ui/container";
import { Tag } from "@/components/ui/tag";
import { getProject, type ProjectDetail } from "@/lib/api/public";
import { formatWorkPeriod } from "@/lib/format";
import { listHref } from "@/lib/search-params";

export async function generateMetadata({ params }: PageProps<"/projects/[slug]">): Promise<Metadata> {
  const project = await getProject((await params).slug);
  if (!project) {
    return { title: "Project not found" };
  }
  return {
    title: project.title,
    description: project.short_description ?? undefined,
    alternates: { canonical: `/projects/${project.slug}` },
    openGraph: project.thumbnail ? { images: [project.thumbnail.url] } : undefined,
  };
}

/** Not prerendered per slug: the first visit renders and caches it (no API needed at build). */
export default function ProjectPage({ params }: PageProps<"/projects/[slug]">) {
  return (
    <Suspense fallback={<ArticleSkeleton />}>
      <ProjectDetails params={params} />
    </Suspense>
  );
}

async function ProjectDetails({ params }: Pick<PageProps<"/projects/[slug]">, "params">) {
  const project = await getProject((await params).slug);
  if (!project) {
    notFound();
  }
  const { thumbnail } = project;

  const period = formatWorkPeriod(project.started_on, project.ended_on);

  return (
    <article>
      <Container className="flex flex-col gap-12 py-16 sm:py-24">
        <Link href="/projects" className="inline-flex w-fit items-center text-sm font-semibold text-muted hover:text-accent pointer-coarse:min-h-11">
          ← All projects
        </Link>
        <header className="flex flex-col gap-8">
          {(period || project.skills.length > 0) && (
            <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
              {period && <p className="text-sm font-semibold text-muted">{period}</p>}
              {project.skills.length > 0 && (
                <ul className="flex flex-wrap gap-2" aria-label="Built with">
                  {project.skills.map((skill) => (
                    <li key={skill.id}>
                      <Tag href={listHref("/projects", { skill: skill.slug })}>{skill.name}</Tag>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
          <h1 className="font-display text-[clamp(3rem,8vw,7.5rem)] leading-[0.88] tracking-[-0.035em]">{project.title}</h1>
          {project.short_description && (
            <p className="max-w-2xl text-xl leading-relaxed text-muted">{project.short_description}</p>
          )}
          {(project.live_url || project.repository_url) && (
            <div className="flex flex-wrap gap-3">
              {project.live_url && (
                <ButtonLink href={project.live_url} target="_blank" rel="noopener noreferrer">
                  Visit the site ↗
                </ButtonLink>
              )}
              {project.repository_url && (
                <ButtonLink href={project.repository_url} variant="secondary" target="_blank" rel="noopener noreferrer">
                  Source code ↗
                </ButtonLink>
              )}
            </div>
          )}
        </header>
        {thumbnail && (
          <div className="overflow-hidden rounded-card border border-line">
            <MediaImage
              src={thumbnail.url}
              alt={thumbnail.alt_text ?? ""}
              width={thumbnail.width}
              height={thumbnail.height}
              sizes="(min-width: 1280px) 1216px, 100vw"
              fetchPriority="high"
              loading="eager"
              className="block h-auto w-full"
            />
          </div>
        )}
        <ProjectSummaryBlock project={project} />
        {project.description && <Markdown className="max-w-3xl text-lg">{project.description}</Markdown>}
        {project.images.length > 0 && (
          <section aria-label="Gallery" className="grid gap-6 md:grid-cols-2">
            {project.images.map(({ id, image }, index) => (
              <div
                key={id}
                data-reveal
                style={{ "--reveal": index % 2 } as CSSProperties}
                className="h-fit overflow-hidden rounded-card border border-line"
              >
                <MediaImage
                  src={image.url}
                  alt={image.alt_text ?? ""}
                  width={image.width}
                  height={image.height}
                  sizes="(min-width: 768px) 600px, 100vw"
                  className="block h-auto w-full"
                />
              </div>
            ))}
          </section>
        )}
      </Container>
    </article>
  );
}

// Column classes by how many of the three are filled, written out so Tailwind finds them.
const SUMMARY_COLUMNS = ["", "md:grid-cols-1", "md:grid-cols-2", "md:grid-cols-3"] as const;

/** Role, problem and result, a sentence or two each: the project at a glance. Empty ones are left out. */
function ProjectSummaryBlock({ project }: { project: ProjectDetail }) {
  const items = [
    { label: "My role", text: project.role },
    { label: "The problem", text: project.problem },
    { label: "The result", text: project.outcome },
  ].filter((item): item is { label: string; text: string } => Boolean(item.text));
  if (items.length === 0) {
    return null;
  }
  return (
    <dl className={`grid gap-8 ${SUMMARY_COLUMNS[items.length]}`}>
      {items.map((item, index) => (
        <div key={item.label} className="flex flex-col gap-4 border-t-[1.5px] border-paper/80 pt-5">
          <dt className="flex items-baseline gap-3">
            <span aria-hidden="true" className="font-display text-5xl leading-none text-accent">
              {String(index + 1).padStart(2, "0")}
            </span>
            <span className="text-sm font-semibold text-muted">{item.label}</span>
          </dt>
          <dd className="max-w-prose text-lg leading-relaxed">{item.text}</dd>
        </div>
      ))}
    </dl>
  );
}
