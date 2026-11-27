import { ScrollHere } from "@/components/scroll-here";
import { SectionHeading } from "@/components/section-heading";
import { SkillGroups } from "@/components/skill-groups";
import { Container } from "@/components/ui/container";
import { getSkills, getSkillSlugsWithProjects, readAtRequestTimeWithoutApi } from "@/lib/api/public";

/**
 * Every skill by category (about page); a skill links to the filtered projects only when it
 * has some. The home page's "See all skills" points here.
 */
export async function SkillsOverview() {
  await readAtRequestTimeWithoutApi();
  const [skills, slugsWithProjects] = await Promise.all([getSkills(), getSkillSlugsWithProjects()]);
  if (skills.length === 0) {
    return null;
  }
  return (
    <section id="skills" className="scroll-mt-16 border-t border-line py-20 sm:py-28">
      <Container className="flex flex-col gap-12">
        <SectionHeading title="Skills" />
        <SkillGroups skills={skills} withProjects={new Set(slugsWithProjects)} />
        <ScrollHere id="skills" />
      </Container>
    </section>
  );
}
