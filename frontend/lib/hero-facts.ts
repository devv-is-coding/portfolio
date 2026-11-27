import type { Experience } from "@/lib/api/public";

/** One cell of the hero's facts row: a large value and the words that say what it counts. */
export type HeroFact = { value: string; label: string };

type HeroFactsInput = {
  /** Published projects (the projects list's total). */
  projectCount: number;
  /** Published projects with a live site. */
  liveProjectCount: number;
  /** Certifications on the site. */
  certificationCount: number;
  experiences: Pick<Experience, "company" | "position" | "start_date" | "is_current">[];
};

function projectsLabel(count: number, live: number): string {
  const noun = count === 1 ? "project" : "projects";
  if (live === 0) {
    return `${noun} in this portfolio`;
  }
  if (live === count) {
    return count === 1 ? "project, live online" : "projects, all live online";
  }
  return `${noun}, ${live} live online`;
}

/**
 * The hero's facts, all from the API, chosen to show work rather than count keywords: the
 * projects (and how many are live), the current role (or, without one, the latest), and the
 * certifications. Each cell only when its data exists, so the row follows what the admin holds.
 */
export function heroFacts({ projectCount, liveProjectCount, certificationCount, experiences }: HeroFactsInput): HeroFact[] {
  const facts: HeroFact[] = [];
  if (projectCount > 0) {
    facts.push({ value: String(projectCount), label: projectsLabel(projectCount, liveProjectCount) });
  }
  const current = experiences.find((entry) => entry.is_current);
  // ISO dates (YYYY-MM-DD) sort as text.
  const latest = experiences.reduce<HeroFactsInput["experiences"][number] | null>(
    (newest, entry) => (!newest || entry.start_date > newest.start_date ? entry : newest),
    null,
  );
  if (current) {
    facts.push({ value: "Now", label: `${current.position} at ${current.company}` });
  } else if (latest) {
    facts.push({ value: latest.start_date.slice(0, 4), label: `${latest.position} at ${latest.company}` });
  }
  if (certificationCount > 0) {
    facts.push({
      value: String(certificationCount),
      label: certificationCount === 1 ? "certification" : "certifications",
    });
  }
  return facts;
}
