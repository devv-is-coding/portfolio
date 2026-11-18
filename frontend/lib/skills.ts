import type { Skill } from "@/lib/api/public";

export type SkillGroup = { category: string; skills: Skill[] };

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
