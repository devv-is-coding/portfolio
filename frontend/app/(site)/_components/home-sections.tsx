import { PostCard } from "@/components/post-card";
import { ProjectCard } from "@/components/project-card";
import { SectionHeading } from "@/components/section-heading";
import { SkillGroups } from "@/components/skill-groups";
import { ButtonLink } from "@/components/ui/button-link";
import { Container } from "@/components/ui/container";
import { getPosts, getProjects, getSkills, readAtRequestTimeWithoutApi } from "@/lib/api/public";

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

export async function SkillsOverview() {
  await readAtRequestTimeWithoutApi();
  const skills = await getSkills();
  if (skills.length === 0) {
    return null;
  }
  return (
    <section className={SECTION}>
      <Container className="flex flex-col gap-12">
        <SectionHeading eyebrow="Toolbox" title="Skills" />
        <SkillGroups skills={skills} />
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
