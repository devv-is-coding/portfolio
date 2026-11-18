import type { Field } from "@/lib/admin/fields";

export const EDUCATION_FIELDS: readonly Field[] = [
  { kind: "text", name: "institution", label: "Institution", required: true, maxLength: 200 },
  { kind: "text", name: "degree", label: "Degree", maxLength: 200 },
  { kind: "text", name: "field_of_study", label: "Field of study", maxLength: 200 },
  { kind: "date", name: "start_date", label: "Start date" },
  { kind: "date", name: "end_date", label: "End date", hint: "Empty: in progress." },
  { kind: "textarea", name: "description", label: "Description", maxLength: 16000, hint: "Markdown." },
];
