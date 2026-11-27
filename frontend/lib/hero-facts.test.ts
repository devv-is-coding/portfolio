import { describe, expect, it } from "vitest";
import { heroFacts } from "@/lib/hero-facts";

const intern = { company: "MidStack", position: "Intern", start_date: "2025-07-18", is_current: false };
const junior = { company: "MidStack", position: "Junior Developer", start_date: "2026-06-01", is_current: true };

describe("heroFacts", () => {
  it("shows the projects with how many are live, the current role and the certifications", () => {
    expect(
      heroFacts({ projectCount: 4, liveProjectCount: 3, certificationCount: 2, experiences: [intern, junior] }),
    ).toEqual([
      { value: "4", label: "projects, 3 live online" },
      { value: "Now", label: "Junior Developer at MidStack" },
      { value: "2", label: "certifications" },
    ]);
  });

  it("names one company once: no separate first-role cell", () => {
    const facts = heroFacts({ projectCount: 0, liveProjectCount: 0, certificationCount: 0, experiences: [intern, junior] });

    expect(facts).toEqual([{ value: "Now", label: "Junior Developer at MidStack" }]);
  });

  it("says when every project is live, and when none is", () => {
    const all = heroFacts({ projectCount: 2, liveProjectCount: 2, certificationCount: 0, experiences: [] });
    const none = heroFacts({ projectCount: 1, liveProjectCount: 0, certificationCount: 1, experiences: [] });

    expect(all.map((fact) => fact.label)).toEqual(["projects, all live online"]);
    expect(none.map((fact) => fact.label)).toEqual(["project in this portfolio", "certification"]);
  });

  it("shows the latest role with its year when none is current", () => {
    const facts = heroFacts({ projectCount: 0, liveProjectCount: 0, certificationCount: 0, experiences: [intern] });

    expect(facts).toEqual([{ value: "2025", label: "Intern at MidStack" }]);
  });

  it("leaves out every cell the API has no data for", () => {
    expect(heroFacts({ projectCount: 0, liveProjectCount: 0, certificationCount: 0, experiences: [] })).toEqual([]);
  });
});
