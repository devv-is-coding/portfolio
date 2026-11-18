import type { Field } from "@/lib/admin/fields";

export const PROFILE_FIELDS: readonly Field[] = [
  { kind: "text", name: "full_name", label: "Full name", required: true, maxLength: 150 },
  { kind: "text", name: "headline", label: "Headline", maxLength: 255, hint: "e.g. Full-stack developer." },
  { kind: "textarea", name: "biography", label: "Biography", maxLength: 10000, rows: 10, hint: "Markdown, shown on the About page." },
  { kind: "text", name: "location", label: "Location", maxLength: 150 },
  { kind: "text", name: "email", label: "Public email", inputType: "email", maxLength: 255, hint: "Shown on About and Contact." },
  { kind: "text", name: "phone", label: "Phone", maxLength: 30 },
  { kind: "media", name: "avatar_media_id", label: "Avatar", mediaKind: "image" },
  { kind: "media", name: "resume_media_id", label: "Résumé (PDF)", mediaKind: "document" },
];

export const SOCIAL_LINK_FIELDS: readonly Field[] = [
  { kind: "text", name: "platform", label: "Platform", required: true, maxLength: 50, hint: "Lowercase letters, digits and dashes, e.g. github, linkedin." },
  { kind: "text", name: "url", label: "URL", inputType: "url", required: true, maxLength: 2048 },
  { kind: "number", name: "display_order", label: "Display order", min: 0, max: 10000 },
];
