import type { Field } from "@/lib/admin/fields";

export const MEDIA_FIELDS: readonly Field[] = [
  { kind: "text", name: "alt_text", label: "Alt text", maxLength: 255, hint: "What the image shows, for screen readers." },
];
