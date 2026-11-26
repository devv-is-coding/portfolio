import type { Field } from "@/lib/admin/fields";
import { PUBLICATION_STATUS_OPTIONS } from "@/lib/admin/options";

export const PROJECT_FIELDS: readonly Field[] = [
  { kind: "text", name: "title", label: "Title", required: true, maxLength: 200 },
  { kind: "text", name: "slug", label: "Slug", maxLength: 220, hint: "The URL: /projects/<slug>. Left empty: made from the title." },
  { kind: "select", name: "status", label: "Status", required: true, options: PUBLICATION_STATUS_OPTIONS, hint: "Only published projects show on the site." },
  { kind: "datetime", name: "published_at", label: "Published at (UTC)", hint: "Empty: set when you publish." },
  { kind: "textarea", name: "short_description", label: "Short description", maxLength: 500, rows: 3, hint: "For the cards, which show up to 3 lines: about 140 characters." },
  { kind: "date", name: "started_on", label: "Work started", hint: "Cards and the project page show the month and year." },
  { kind: "date", name: "ended_on", label: "Work ended", hint: "Empty: still going." },
  { kind: "text", name: "role", label: "My role", maxLength: 200, hint: "e.g. Full-stack developer, solo." },
  { kind: "textarea", name: "problem", label: "The problem", maxLength: 500, rows: 3, hint: "A sentence or two: what needed solving." },
  { kind: "textarea", name: "outcome", label: "The result", maxLength: 500, rows: 3, hint: "A sentence or two: what changed." },
  { kind: "textarea", name: "description", label: "Description", maxLength: 100000, rows: 14, hint: "Markdown." },
  { kind: "media", name: "thumbnail_media_id", label: "Thumbnail", mediaKind: "image" },
  { kind: "text", name: "live_url", label: "Live URL", inputType: "url", maxLength: 2048 },
  { kind: "text", name: "repository_url", label: "Repository URL", inputType: "url", maxLength: 2048 },
  { kind: "checkbox", name: "is_featured", label: "Featured on the home page" },
  { kind: "number", name: "display_order", label: "Display order", min: 0, max: 10000, hint: "Lower comes first." },
];

export const IMAGE_EDIT_FIELDS: readonly Field[] = [
  { kind: "text", name: "alt_text", label: "Alt text", maxLength: 255 },
  { kind: "number", name: "display_order", label: "Display order", min: 0, max: 10000 },
];
