import type { Experience } from "@/lib/api/public";

/** One cell of the hero's facts row: a large value and the words that say what it counts. */
export type HeroFact = { value: string; label: string };

type HeroFactsInput = {
  /** Published projects (the projects list's total). */
  projectCount: number;
  /** Skills on the site. */
  skillCount: number;
  experiences: Pick<Experience, "company" | "position" | "start_date" | "is_current">[];
};

/**
 * The hero's facts, all from the API: each cell only when its data exists, so the row follows
 * what the admin holds (no projects yet: no projects cell).
 */
export function heroFacts({ projectCount, skillCount, experiences }: HeroFactsInput): HeroFact[] {
  const facts: HeroFact[] = [];
  if (projectCount > 0) {
    facts.push({
      value: String(projectCount),
      label: projectCount === 1 ? "project in this portfolio" : "projects in this portfolio",
    });
  }
  if (skillCount > 0) {
    facts.push({ value: String(skillCount), label: skillCount === 1 ? "tool or language" : "tools and languages" });
  }
  // ISO dates (YYYY-MM-DD) sort as text.
  const first = experiences.reduce<HeroFactsInput["experiences"][number] | null>(
    (earliest, entry) => (!earliest || entry.start_date < earliest.start_date ? entry : earliest),
    null,
  );
  if (first) {
    facts.push({ value: first.start_date.slice(0, 4), label: `first role, at ${first.company}` });
  }
  const current = experiences.find((entry) => entry.is_current);
  if (current) {
    facts.push({ value: "Now", label: `${current.position} at ${current.company}` });
  }
  return facts;
}
