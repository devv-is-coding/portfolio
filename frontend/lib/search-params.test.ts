import { describe, expect, it } from "vitest";
import { firstParam, listHref, pageParam } from "@/lib/search-params";

describe("firstParam", () => {
  it.each([
    ["python", "python"],
    [["a", "b"], "a"],
    ["  ", undefined],
    [undefined, undefined],
    [[], undefined],
  ])("%j -> %j", (value, expected) => {
    expect(firstParam(value)).toBe(expected);
  });
});

describe("pageParam", () => {
  it.each([
    ["3", 3],
    [["2", "5"], 2],
    ["0", 1],
    ["-4", 1],
    ["1.5", 1],
    ["abc", 1],
    [undefined, 1],
  ])("%j -> %d", (value, expected) => {
    expect(pageParam(value)).toBe(expected);
  });
});

describe("listHref", () => {
  it("keeps filters and leaves out empty values and page 1", () => {
    expect(listHref("/blog", { category: "notes", tag: undefined, page: 1 })).toBe("/blog?category=notes");
    expect(listHref("/blog", { category: "a b", page: 2 })).toBe("/blog?category=a+b&page=2");
    expect(listHref("/projects", { skill: "", page: 1 })).toBe("/projects");
  });
});
