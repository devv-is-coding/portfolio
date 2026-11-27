import { getExperiences, getProjects, getSkills, readAtRequestTimeWithoutApi } from "@/lib/api/public";
import { cn } from "@/lib/cn";
import { heroFacts } from "@/lib/hero-facts";

// Columns from md up follow the number of cells, so two facts never sit in a row of four.
const COLUMNS = ["", "md:grid-cols-1", "md:grid-cols-2", "md:grid-cols-3", "md:grid-cols-4"] as const;

/**
 * The hero's facts row, streamed from the API (lib/hero-facts.ts decides the cells). Nothing
 * when the API has none of the data; the row around it keeps its height either way.
 */
export async function HeroFacts() {
  await readAtRequestTimeWithoutApi();
  const [projects, skills, experiences] = await Promise.all([
    getProjects({ size: 1 }),
    getSkills(),
    getExperiences(),
  ]);
  const facts = heroFacts({ projectCount: projects.total, skillCount: skills.length, experiences });
  if (facts.length === 0) {
    return null;
  }
  return (
    <ul className={cn("grid h-full grid-cols-2", COLUMNS[facts.length])}>
      {facts.map((fact, index) => (
        <li
          key={fact.label}
          className={cn(
            "flex items-center gap-3 py-3 md:py-0",
            // A rule between neighbours: on phones between the two columns, from md between all.
            index % 2 === 1 && "border-l border-line pl-4",
            index > 0 && "md:border-l md:border-line md:pl-5",
            index >= 2 && "max-md:border-t max-md:border-line",
          )}
        >
          <span className="font-display text-[clamp(2rem,3vw,2.75rem)] leading-none tracking-[-0.03em]">
            {fact.value}
          </span>
          <span className="max-w-[18ch] text-sm leading-snug text-muted">{fact.label}</span>
        </li>
      ))}
    </ul>
  );
}
