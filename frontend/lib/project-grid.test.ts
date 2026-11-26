import { describe, expect, it } from "vitest";
import { projectGridClass } from "@/lib/project-grid";

describe("projectGridClass", () => {
  it("keeps a lone card at a readable width", () => {
    expect(projectGridClass(1)).toContain("md:max-w-xl");
    expect(projectGridClass(1)).not.toContain("grid-cols");
  });

  it("gives two cards two columns, with no empty third", () => {
    expect(projectGridClass(2)).toContain("md:grid-cols-2");
    expect(projectGridClass(2)).not.toContain("lg:grid-cols-3");
  });

  it("uses three columns from three cards on", () => {
    expect(projectGridClass(3)).toContain("lg:grid-cols-3");
    expect(projectGridClass(40)).toContain("lg:grid-cols-3");
  });
});
