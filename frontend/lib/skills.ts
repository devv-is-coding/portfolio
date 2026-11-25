import type { Skill } from "@/lib/api/public";

export type SkillGroup = { category: string; skills: Skill[] };

// How many skills the home page shows: the first ones in display order, which the admin sets.
export const CORE_SKILL_COUNT = 6;

/**
 * The skills to offer as project filters: those with projects, plus the one filtered on right
 * now (a visitor who arrived with it in the URL can see what's filtered and clear it).
 */
export function filterSkills(skills: readonly Skill[], withProjects: ReadonlySet<string>, current?: string): Skill[] {
  return skills.filter((skill) => withProjects.has(skill.slug) || skill.slug === current);
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
