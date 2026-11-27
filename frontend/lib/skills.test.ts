import { describe, expect, it } from "vitest";
import type { Skill } from "@/lib/api/public";
import { filterSkills, groupSkills, slugsWithProjects } from "@/lib/skills";

function skill(id: number, name: string, category: string | null): Skill {
  return {
    id,
    name,
    slug: name.toLowerCase(),
    category,
    icon_media_id: null,
    icon: null,
    display_order: id,
    created_at: "2026-01-01T00:00:00",
    updated_at: "2026-01-01T00:00:00",
  };
}

describe("groupSkills", () => {
  it("groups in display order and puts uncategorized skills last", () => {
    const groups = groupSkills([
      skill(1, "Git", null),
      skill(2, "Python", "Backend"),
      skill(3, "React", "Frontend"),
      skill(4, "FastAPI", "Backend"),
      skill(5, "Docker", "  "),
    ]);

    expect(groups.map((group) => [group.category, group.skills.map((s) => s.name)])).toEqual([
      ["Backend", ["Python", "FastAPI"]],
      ["Frontend", ["React"]],
      ["Other", ["Git", "Docker"]],
    ]);
  });

  it("returns no groups for no skills", () => {
    expect(groupSkills([])).toEqual([]);
  });
});

describe("filterSkills", () => {
  const skills = [skill(1, "FastAPI", "backend"), skill(2, "WordPress", "web"), skill(3, "Shopify", "web")];

  it("keeps every skill with projects, in display order", () => {
    expect(filterSkills(skills, { shopify: 2, wordpress: 1 }).map((s) => s.name)).toEqual(["WordPress", "Shopify"]);
  });

  it("keeps the skill filtered on right now, even without projects", () => {
    expect(filterSkills(skills, { shopify: 1 }, "fastapi").map((s) => s.name)).toEqual(["FastAPI", "Shopify"]);
  });

  it("offers nothing when no project has skills", () => {
    expect(filterSkills(skills, {})).toEqual([]);
  });
});

describe("slugsWithProjects", () => {
  it("lists the skills with at least one project", () => {
    expect([...slugsWithProjects({ fastapi: 2, shopify: 0 })]).toEqual(["fastapi"]);
  });
});
