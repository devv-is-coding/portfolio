import type { Field } from "@/lib/admin/fields";

export const EXPERIENCE_FIELDS: readonly Field[] = [
  { kind: "text", name: "position", label: "Position", required: true, maxLength: 200 },
  { kind: "text", name: "company", label: "Company", required: true, maxLength: 200 },
  { kind: "text", name: "employment_type", label: "Employment type", maxLength: 50, hint: "e.g. full-time, contract." },
  { kind: "text", name: "location", label: "Location", maxLength: 150 },
  { kind: "date", name: "start_date", label: "Start date", required: true },
  { kind: "date", name: "end_date", label: "End date", hint: "Empty: the current job." },
  { kind: "textarea", name: "description", label: "Description", maxLength: 100000, hint: "Markdown." },
  { kind: "number", name: "display_order", label: "Display order", min: 0, max: 10000, hint: "Orders jobs with the same start date." },
];
