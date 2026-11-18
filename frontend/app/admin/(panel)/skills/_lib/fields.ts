import type { Field } from "@/lib/admin/fields";

export const SKILL_FIELDS: readonly Field[] = [
  { kind: "text", name: "name", label: "Name", required: true, maxLength: 100 },
  { kind: "text", name: "slug", label: "Slug", maxLength: 120, hint: "Left empty: made from the name." },
  { kind: "text", name: "category", label: "Category", maxLength: 100, hint: "Groups skills on the site, e.g. Backend." },
  { kind: "media", name: "icon_media_id", label: "Icon", mediaKind: "image" },
  { kind: "number", name: "display_order", label: "Display order", min: 0, max: 10000, hint: "Lower comes first." },
];
