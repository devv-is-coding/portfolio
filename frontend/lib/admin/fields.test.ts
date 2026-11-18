import { describe, expect, it } from "vitest";
import { type Field, inputValue, parseFields } from "@/lib/admin/fields";

const FIELDS: Field[] = [
  { kind: "text", name: "name", label: "Name", required: true },
  { kind: "text", name: "category", label: "Category" },
  { kind: "textarea", name: "description", label: "Description" },
  { kind: "number", name: "display_order", label: "Order" },
  { kind: "date", name: "start_date", label: "Start" },
  { kind: "datetime", name: "published_at", label: "Published" },
  { kind: "checkbox", name: "is_featured", label: "Featured" },
  { kind: "select", name: "status", label: "Status", options: [{ value: "draft", label: "Draft" }] },
  { kind: "media", name: "icon_media_id", label: "Icon", mediaKind: "image" },
];

function form(values: Record<string, string>): FormData {
  const data = new FormData();
  for (const [key, value] of Object.entries(values)) {
    data.set(key, value);
  }
  return data;
}

describe("parseFields", () => {
  it("turns filled-in values into API types", () => {
    const body = parseFields(
      FIELDS,
      form({
        name: "  FastAPI ",
        category: "Backend",
        description: "Fast.",
        display_order: "3",
        start_date: "2024-03-01",
        published_at: "2026-11-18T10:30",
        is_featured: "on",
        status: "draft",
        icon_media_id: "12",
      }),
    );

    expect(body).toEqual({
      name: "FastAPI",
      category: "Backend",
      description: "Fast.",
      display_order: 3,
      start_date: "2024-03-01",
      published_at: "2026-11-18T10:30:00",
      is_featured: true,
      status: "draft",
      icon_media_id: 12,
    });
  });

  it("clears empty optional values, keeps empty required text, leaves out empty numbers and dates", () => {
    const body = parseFields(FIELDS, form({ name: "", category: " ", display_order: "", status: "" }));

    expect(body).toEqual({
      name: "",
      category: null,
      description: null,
      start_date: null,
      is_featured: false,
      status: null,
      icon_media_id: null,
    });
  });
});

describe("inputValue", () => {
  it("shows API values in inputs", () => {
    expect(inputValue(FIELDS[5], "2026-11-18T10:30:00")).toBe("2026-11-18T10:30");
    expect(inputValue(FIELDS[3], 4)).toBe("4");
    expect(inputValue(FIELDS[1], null)).toBe("");
    expect(inputValue(FIELDS[6], true)).toBe("");
  });
});
