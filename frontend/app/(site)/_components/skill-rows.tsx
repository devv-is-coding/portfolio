import type { CSSProperties } from "react";
import { PosterHeading } from "@/components/poster-heading";
import { Container } from "@/components/ui/container";
import { TextLink } from "@/components/ui/text-link";
import { getSkillProjectCounts, getSkills, readAtRequestTimeWithoutApi } from "@/lib/api/public";
import { groupSkills, HOME_SKILL_GROUPS, slugsWithProjects } from "@/lib/skills";

/**
 * The skills, one row per category in the admin's order: the category as a small label, the
 * skills themselves as the large type (what he can do is the point, not the category's name).
 * The categories are the admin's, as they are. A skill links to the projects that use
 * it, and only when there are some: those are underlined. Hovering a row floods it with gold.
 * The first few rows, then a link to the full list on the about page. Left out without skills.
 */
export async function SkillRows() {
  await readAtRequestTimeWithoutApi();
  const [skills, projectCounts] = await Promise.all([getSkills(), getSkillProjectCounts()]);
  const groups = groupSkills(skills);
  if (groups.length === 0) {
    return null;
  }
  const shown = groups.slice(0, HOME_SKILL_GROUPS);
  const withProjects = slugsWithProjects(projectCounts);
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
              className="flood-row relative isolate grid gap-3 border-b border-line py-6 md:grid-cols-[minmax(0,1fr)_minmax(0,4fr)] md:items-baseline md:gap-8 md:py-8"
            >
              <h3 className="flood-soft text-sm font-semibold text-muted">{group.category}</h3>
              <ul
                className="flood-title flex flex-wrap items-baseline gap-x-3 gap-y-1 font-display text-[clamp(1.75rem,3.4vw,3.25rem)] leading-none tracking-[-0.02em]"
                aria-label={`${group.category} skills`}
              >
                {group.skills.map((skill, position) => (
                  <li key={skill.id} className="flex items-baseline gap-3">
                    {withProjects.has(skill.slug) ? (
                      // 44 px tall on touch screens, like every other tap target.
                      <a
                        href={`/projects?skill=${encodeURIComponent(skill.slug)}`}
                        className="inline-flex items-center underline decoration-current/35 decoration-[0.06em] underline-offset-[0.14em] transition-colors hover:decoration-current pointer-coarse:min-h-11"
                      >
                        {skill.name}
                      </a>
                    ) : (
                      <span>{skill.name}</span>
                    )}
                    {/* After the skill, not before the next: a wrapped line ends on the slash
                        instead of starting with one. */}
                    {position < group.skills.length - 1 && (
                      <span aria-hidden="true" className="flood-soft text-muted">
                        /
                      </span>
                    )}
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
