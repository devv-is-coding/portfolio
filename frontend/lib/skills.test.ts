import { describe, expect, it } from "vitest";
import type { Skill } from "@/lib/api/public";
import { groupSkills } from "@/lib/skills";

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
