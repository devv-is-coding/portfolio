import type { Field } from "@/lib/admin/fields";

export const TAGS_FIELDS: readonly Field[] = [
  { kind: "text", name: "name", label: "Name", required: true, maxLength: 100 },
  { kind: "text", name: "slug", label: "Slug", maxLength: 120, hint: "Left empty: made from the name." },
];
