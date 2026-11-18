import { Tag } from "@/components/ui/tag";
import type { Skill } from "@/lib/api/public";
import { groupSkills } from "@/lib/skills";

/** Skills by category, as rows of tags (home and about pages). */
export function SkillGroups({ skills }: { skills: readonly Skill[] }) {
  return (
    <dl className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
      {groupSkills(skills).map((group) => (
        <div key={group.category} className="flex flex-col gap-4 border-t border-line pt-6">
          <dt className="font-mono text-xs uppercase tracking-[0.2em] text-muted">{group.category}</dt>
          <dd>
            <ul className="flex flex-wrap gap-2">
              {group.skills.map((skill) => (
                <li key={skill.id}>
                  <Tag href={`/projects?skill=${encodeURIComponent(skill.slug)}`}>{skill.name}</Tag>
                </li>
              ))}
            </ul>
          </dd>
        </div>
      ))}
    </dl>
  );
}
