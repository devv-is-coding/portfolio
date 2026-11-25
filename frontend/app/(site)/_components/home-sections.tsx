import { PostCard } from "@/components/post-card";
import { ProjectCard } from "@/components/project-card";
import { SectionHeading } from "@/components/section-heading";
import { SkillGroups, SkillTags } from "@/components/skill-groups";
import { ScrollHere } from "@/components/scroll-here";
import { ButtonLink } from "@/components/ui/button-link";
import { Container } from "@/components/ui/container";
import {
  getPosts,
  getProjects,
  getSkills,
  getSkillSlugsWithProjects,
  readAtRequestTimeWithoutApi,
} from "@/lib/api/public";
import { CORE_SKILL_COUNT } from "@/lib/skills";

const SECTION = "border-t border-line py-20 sm:py-28";

/** The featured projects, or the first ones when none is featured; hidden without projects. */
export async function FeaturedProjects() {
  await readAtRequestTimeWithoutApi();
  const featured = await getProjects({ featured: true, size: 3 });
  const projects = featured.items.length > 0 ? featured.items : (await getProjects({ size: 3 })).items;
  if (projects.length === 0) {
    return null;
  }
  return (
    // The motion code pins this section and slides the cards sideways as the page scrolls
    // (lib/motion "sideways"); clipped, so the row never adds a sideways scroll.
    <section data-motion="sideways" className={`${SECTION} overflow-x-clip`}>
      <Container className="flex flex-col gap-12">
        <SectionHeading
          eyebrow="Selected work"
          title="Projects"
          action={
            <ButtonLink href="/projects" variant="outline">
              All projects
            </ButtonLink>
          }
        />
        <div data-motion-track className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              // In the sideways row a card is 80vw / 55vw / up to 576 px wide (globals.css).
              sizes="(min-width: 1024px) 576px, (min-width: 768px) 55vw, 100vw"
            />
          ))}
        </div>
      </Container>
    </section>
  );
}

/**
 * The skills. `core` (home page): the first few in display order as one row, with a link to
 * the full list; otherwise (about page) every skill by category. Either way a skill links to
 * the filtered projects only when it has some.
 */
export async function SkillsOverview({ core = false }: { core?: boolean }) {
  await readAtRequestTimeWithoutApi();
  const [skills, slugsWithProjects] = await Promise.all([getSkills(), getSkillSlugsWithProjects()]);
  if (skills.length === 0) {
    return null;
  }
  const withProjects = new Set(slugsWithProjects);
  const shown = core ? skills.slice(0, CORE_SKILL_COUNT) : skills;
  const more = core && skills.length > shown.length;
  return (
    <section id={core ? undefined : "skills"} className={`${SECTION} scroll-mt-16`}>
      <Container className="flex flex-col gap-12">
        <SectionHeading
          eyebrow="Toolbox"
          title="Skills"
          action={
            more ? (
              <ButtonLink href="/about#skills" variant="outline">
                All skills
              </ButtonLink>
            ) : undefined
          }
        />
        {core ? (
          <SkillTags skills={shown} withProjects={withProjects} />
        ) : (
          <>
            <SkillGroups skills={shown} withProjects={withProjects} />
            {/* The home page's "All skills" points here. */}
            <ScrollHere id="skills" />
          </>
        )}
      </Container>
    </section>
  );
}

export async function LatestPosts() {
  await readAtRequestTimeWithoutApi();
  const { items } = await getPosts({ size: 3 });
  if (items.length === 0) {
    return null;
  }
  return (
    <section className={SECTION}>
      <Container className="flex flex-col gap-8">
        <SectionHeading
          eyebrow="Writing"
          title="Latest posts"
          action={
            <ButtonLink href="/blog" variant="outline">
              All posts
            </ButtonLink>
          }
        />
        <div>
          {items.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      </Container>
    </section>
  );
}
