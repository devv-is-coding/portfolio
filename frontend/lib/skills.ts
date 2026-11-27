import type { Skill } from "@/lib/api/public";

export type SkillGroup = { category: string; skills: Skill[] };

// How many skill categories the home page shows: the first ones in display order (the admin
// sets it); the about page lists them all.
export const HOME_SKILL_GROUPS = 6;

/** The slugs of the skills at least one project uses, from getSkillProjectCounts(). */
export function slugsWithProjects(counts: Readonly<Record<string, number>>): ReadonlySet<string> {
  return new Set(Object.keys(counts).filter((slug) => (counts[slug] ?? 0) > 0));
}

/**
 * The skills to offer as project filters: every skill a published project uses, in the
 * admin's display order, plus the one filtered on right now (a visitor who arrived with it in
 * the URL can see what's filtered and clear it).
 */
export function filterSkills(skills: readonly Skill[], counts: Readonly<Record<string, number>>, current?: string): Skill[] {
  return skills.filter((skill) => (counts[skill.slug] ?? 0) > 0 || skill.slug === current);
}

const UNCATEGORIZED = "Other";

/**
 * Skills grouped by category, in the order the API returns them (display order): a group
 * appears where its first skill does, skills without a category come last as "Other".
 */
export function groupSkills(skills: readonly Skill[]): SkillGroup[] {
  const groups = new Map<string, Skill[]>();
  for (const skill of skills) {
    const category = skill.category?.trim() || UNCATEGORIZED;
    groups.set(category, [...(groups.get(category) ?? []), skill]);
  }
  const ordered = [...groups].map(([category, items]) => ({ category, skills: items }));
  return [
    ...ordered.filter((group) => group.category !== UNCATEGORIZED),
    ...ordered.filter((group) => group.category === UNCATEGORIZED),
  ];
}
