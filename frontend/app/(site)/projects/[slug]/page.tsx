import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { Markdown } from "@/components/markdown";
import { MediaImage } from "@/components/media-image";
import { ButtonLink } from "@/components/ui/button-link";
import { Container } from "@/components/ui/container";
import { Eyebrow } from "@/components/ui/eyebrow";
import { Tag } from "@/components/ui/tag";
import { getProject } from "@/lib/api/public";
import { formatMonthYear } from "@/lib/format";
import { listHref } from "@/lib/search-params";

export async function generateMetadata({ params }: PageProps<"/projects/[slug]">): Promise<Metadata> {
  const project = await getProject((await params).slug);
  if (!project) {
    return { title: "Project not found" };
  }
  return {
    title: project.title,
    description: project.short_description ?? undefined,
    openGraph: project.thumbnail ? { images: [project.thumbnail.url] } : undefined,
  };
}

/** Not prerendered per slug: the first visit renders and caches it (no API needed at build). */
export default function ProjectPage({ params }: PageProps<"/projects/[slug]">) {
  return (
    <Suspense fallback={<Container className="h-[60vh] py-24" />}>
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

  return (
    <article>
      <Container className="flex flex-col gap-10 py-16 sm:py-24">
        <Link href="/projects" className="w-fit font-mono text-xs uppercase tracking-[0.2em] text-muted hover:text-accent">
          ← All projects
        </Link>
        <header className="flex flex-col gap-6">
          <Eyebrow>{project.published_at ? formatMonthYear(project.published_at) : "Project"}</Eyebrow>
          <h1 className="font-display text-display font-extrabold uppercase">{project.title}</h1>
          {project.short_description && <p className="max-w-2xl text-xl text-muted">{project.short_description}</p>}
          <div className="flex flex-wrap gap-3">
            {project.live_url && (
              <ButtonLink href={project.live_url} target="_blank" rel="noopener noreferrer">
                Visit the site ↗
              </ButtonLink>
            )}
            {project.repository_url && (
              <ButtonLink href={project.repository_url} variant="outline" target="_blank" rel="noopener noreferrer">
                Source code ↗
              </ButtonLink>
            )}
          </div>
          {project.skills.length > 0 && (
            <ul className="flex flex-wrap gap-2" aria-label="Built with">
              {project.skills.map((skill) => (
                <li key={skill.id}>
                  <Tag href={listHref("/projects", { skill: skill.slug })}>{skill.name}</Tag>
                </li>
              ))}
            </ul>
          )}
        </header>
        {thumbnail && (
          <MediaImage
            src={thumbnail.url}
            alt={thumbnail.alt_text ?? ""}
            width={thumbnail.width}
            height={thumbnail.height}
            sizes="(min-width: 1280px) 1216px, 100vw"
            fetchPriority="high"
            loading="eager"
            className="h-auto w-full rounded-2xl border border-line"
          />
        )}
        {project.description && <Markdown className="max-w-3xl text-lg">{project.description}</Markdown>}
        {project.images.length > 0 && (
          <section aria-label="Gallery" className="grid gap-6 md:grid-cols-2">
            {project.images.map(({ id, image }) => (
              <MediaImage
                key={id}
                src={image.url}
                alt={image.alt_text ?? ""}
                width={image.width}
                height={image.height}
                sizes="(min-width: 768px) 600px, 100vw"
                className="h-auto w-full rounded-2xl border border-line"
              />
            ))}
          </section>
        )}
      </Container>
    </article>
  );
}
