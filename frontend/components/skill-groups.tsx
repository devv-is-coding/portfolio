import { Tag } from "@/components/ui/tag";
import type { Skill } from "@/lib/api/public";
import { groupSkills } from "@/lib/skills";

type SkillsProps = {
  skills: readonly Skill[];
  /** Slugs of the skills with projects: only those link to the filtered project list. */
  withProjects: ReadonlySet<string>;
};

/** Skills by category, as rows of tags (about page). */
export function SkillGroups({ skills, withProjects }: SkillsProps) {
  return (
    <dl className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
      {groupSkills(skills).map((group) => (
        <div key={group.category} className="flex flex-col gap-4 border-t border-line pt-6">
          <dt className="font-mono text-xs uppercase tracking-[0.2em] text-muted">{group.category}</dt>
          <dd>
            <SkillTags skills={group.skills} withProjects={withProjects} />
          </dd>
        </div>
      ))}
    </dl>
  );
}

/** One row of skill tags; a skill with no project behind it is a plain label, not a dead end. */
export function SkillTags({ skills, withProjects }: SkillsProps) {
  return (
    <ul className="flex flex-wrap gap-2">
      {skills.map((skill) => (
        <li key={skill.id}>
          <Tag href={withProjects.has(skill.slug) ? `/projects?skill=${encodeURIComponent(skill.slug)}` : undefined}>
            {skill.name}
          </Tag>
        </li>
      ))}
    </ul>
  );
}
