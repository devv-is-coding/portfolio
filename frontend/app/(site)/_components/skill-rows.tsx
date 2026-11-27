import type { CSSProperties } from "react";
import { PosterHeading } from "@/components/poster-heading";
import { Container } from "@/components/ui/container";
import { Tag } from "@/components/ui/tag";
import { TextLink } from "@/components/ui/text-link";
import { getSkills, getSkillSlugsWithProjects, readAtRequestTimeWithoutApi } from "@/lib/api/public";
import { groupSkills, HOME_SKILL_GROUPS } from "@/lib/skills";

/**
 * The skills as one huge row per category, in the admin's order: the first few categories,
 * then a link to the full list on the about page. A skill links to the projects that use it,
 * and only when there are some. Hovering a row floods it with gold. Left out without skills.
 */
export async function SkillRows() {
  await readAtRequestTimeWithoutApi();
  const [skills, slugsWithProjects] = await Promise.all([getSkills(), getSkillSlugsWithProjects()]);
  const groups = groupSkills(skills);
  if (groups.length === 0) {
    return null;
  }
  const shown = groups.slice(0, HOME_SKILL_GROUPS);
  const withProjects = new Set(slugsWithProjects);
  return (
    // overflow-x-clip: the flood runs to the screen's edges, never past them.
    <section className="below-fold overflow-x-clip border-t border-line py-20 sm:py-28">
      <Container className="flex flex-col gap-12">
        <PosterHeading
          title="Skills"
          action={groups.length > shown.length ? <TextLink href="/about#skills">See all skills</TextLink> : undefined}
        />
        <ul className="border-t border-line">
          {shown.map((group, index) => (
            <li
              key={group.category}
              data-reveal
              style={{ "--reveal": index } as CSSProperties}
              className="flood-row relative isolate grid gap-4 border-b border-line py-7 md:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] md:items-center md:gap-8 md:py-9"
            >
              <h3 className="flood-title font-display text-[clamp(2.5rem,5.5vw,5.5rem)] leading-[0.9] tracking-[-0.03em]">
                {group.category}
              </h3>
              {/* skill-tags: on a flooded row the tags turn ink (globals.css, one rule for all). */}
              <ul className="skill-tags flex flex-wrap gap-2" aria-label={`${group.category} skills`}>
                {group.skills.map((skill) => (
                  <li key={skill.id}>
                    <Tag href={withProjects.has(skill.slug) ? `/projects?skill=${encodeURIComponent(skill.slug)}` : undefined}>
                      {skill.name}
                    </Tag>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      </Container>
    </section>
  );
}
