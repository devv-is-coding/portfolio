import type { Metadata } from "next";
import { Suspense } from "react";
import { Pagination } from "@/components/pagination";
import { ProjectCard } from "@/components/project-card";
import { SectionHeading } from "@/components/section-heading";
import { ProjectListSkeleton } from "@/components/skeletons";
import { Container } from "@/components/ui/container";
import { EmptyState } from "@/components/ui/empty-state";
import { Tag } from "@/components/ui/tag";
import { getProjects, getSkills } from "@/lib/api/public";
import { firstParam, listHref, pageParam } from "@/lib/search-params";
import { SITE } from "@/lib/site";

export const metadata: Metadata = {
  title: "Projects",
  description: `Projects built by ${SITE.name}.`,
  alternates: { canonical: "/projects" },
};

const PAGE_SIZE = 12;

export default function ProjectsPage({ searchParams }: PageProps<"/projects">) {
  return (
    <Container className="flex flex-col gap-12 py-16 sm:py-24">
      <SectionHeading as="h1" eyebrow="Work" title="Projects" />
      {/* The fallback fills the screen, so the footer never jumps when the list streams in. */}
      <Suspense fallback={<ProjectListSkeleton />}>
        <ProjectList searchParams={searchParams} />
      </Suspense>
    </Container>
  );
}

async function ProjectList({ searchParams }: Pick<PageProps<"/projects">, "searchParams">) {
  const params = await searchParams;
  const page = pageParam(params.page);
  const skill = firstParam(params.skill);
  const [projects, skills] = await Promise.all([
    getProjects({ page, size: PAGE_SIZE, skill }),
    getSkills(),
  ]);

  // At least a screen tall, like the fallback: a short (empty) list never pulls the footer up.
  return (
    <div className="flex min-h-svh flex-col gap-10">
      {skills.length > 0 && (
        <nav aria-label="Filter by skill">
          <ul className="flex flex-wrap gap-2">
            <li>
              <Tag href="/projects" active={!skill}>
                All
              </Tag>
            </li>
            {skills.map((item) => (
              <li key={item.id}>
                <Tag href={listHref("/projects", { skill: item.slug })} active={item.slug === skill}>
                  {item.name}
                </Tag>
              </li>
            ))}
          </ul>
        </nav>
      )}
      {projects.items.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {projects.items.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              headingLevel="h2"
              sizes="(min-width: 1024px) 400px, (min-width: 768px) 50vw, 100vw"
            />
          ))}
        </div>
      ) : (
        <EmptyState title={skill || page > 1 ? "No projects here" : "No projects yet"}>
          {skill || page > 1 ? "Try another filter or the first page." : "The first ones are on their way."}
        </EmptyState>
      )}
      <Pagination
        page={projects.page}
        pages={projects.pages}
        href={(target) => listHref("/projects", { skill, page: target })}
      />
    </div>
  );
}
