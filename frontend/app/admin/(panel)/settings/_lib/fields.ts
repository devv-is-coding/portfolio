import type { Field } from "@/lib/admin/fields";

const VALUE: Field = {
  kind: "textarea",
  name: "value",
  label: "Value (JSON)",
  required: true,
  maxLength: 10000,
  rows: 4,
  hint: 'JSON: "text", 42, true, ["a", "b"] or {"key": "value"}.',
};

export const SETTING_NEW_FIELDS: readonly Field[] = [
  {
    kind: "text",
    name: "key",
    label: "Key",
    required: true,
    maxLength: 150,
    hint: "Dotted lowercase, e.g. site.tagline. Keys under site. and seo. are public.",
  },
  VALUE,
];

export const SETTING_EDIT_FIELDS: readonly Field[] = [VALUE];
