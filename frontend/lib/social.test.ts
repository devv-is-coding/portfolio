import { describe, expect, it } from "vitest";
import { platformName } from "@/lib/social";

describe("platformName", () => {
  it.each([
    ["linkedin", "LinkedIn"],
    ["github", "GitHub"],
    ["facebook", "Facebook"],
    ["LINKEDIN", "LinkedIn"],
    ["  youtube ", "YouTube"],
    ["twitter", "X"],
    ["stackoverflow", "Stack Overflow"],
  ])("spells %j as the platform does", (typed, expected) => {
    expect(platformName(typed)).toBe(expected);
  });

  it("capitalizes an unknown all-lowercase name", () => {
    expect(platformName("codepen")).toBe("Codepen");
  });

  it("keeps an unknown name typed with capitals", () => {
    expect(platformName("CodePen")).toBe("CodePen");
  });
});
