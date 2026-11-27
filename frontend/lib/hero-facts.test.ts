import { describe, expect, it } from "vitest";
import { heroFacts } from "@/lib/hero-facts";

const intern = { company: "MidStack", position: "Intern", start_date: "2025-07-18", is_current: false };
const junior = { company: "MidStack", position: "Junior Developer", start_date: "2026-06-01", is_current: true };

describe("heroFacts", () => {
  it("counts projects and skills, then the first and the current role", () => {
    expect(heroFacts({ projectCount: 3, skillCount: 31, experiences: [junior, intern] })).toEqual([
      { value: "3", label: "projects in this portfolio" },
      { value: "31", label: "tools and languages" },
      { value: "2025", label: "first role, at MidStack" },
      { value: "Now", label: "Junior Developer at MidStack" },
    ]);
  });

  it("uses the singular for one", () => {
    const facts = heroFacts({ projectCount: 1, skillCount: 1, experiences: [] });

    expect(facts.map((fact) => fact.label)).toEqual(["project in this portfolio", "tool or language"]);
  });

  it("leaves out every cell the API has no data for", () => {
    expect(heroFacts({ projectCount: 0, skillCount: 0, experiences: [] })).toEqual([]);
  });

  it("shows no current role when none is marked current", () => {
    const facts = heroFacts({ projectCount: 0, skillCount: 0, experiences: [intern] });

    expect(facts).toEqual([{ value: "2025", label: "first role, at MidStack" }]);
  });
});
