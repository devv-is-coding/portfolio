import type { Field } from "@/lib/admin/fields";
import { PUBLICATION_STATUS_OPTIONS } from "@/lib/admin/options";

/** The post form; the categories are the select's choices (parsing works without them). */
export function postFields(categories: readonly { id: number; name: string }[] = []): readonly Field[] {
  return [
    { kind: "text", name: "title", label: "Title", required: true, maxLength: 255 },
    { kind: "text", name: "slug", label: "Slug", maxLength: 280, hint: "The URL: /blog/<slug>. Left empty: made from the title." },
    { kind: "select", name: "status", label: "Status", required: true, options: PUBLICATION_STATUS_OPTIONS, hint: "Only published posts show on the site." },
    { kind: "datetime", name: "published_at", label: "Published at (UTC)", hint: "Empty: set when you publish." },
    {
      kind: "select",
      name: "category_id",
      label: "Category",
      options: categories.map((category) => ({ value: String(category.id), label: category.name })),
    },
    { kind: "textarea", name: "excerpt", label: "Excerpt", maxLength: 500, rows: 3, hint: "Shown in lists and search results." },
    { kind: "textarea", name: "content", label: "Content", required: true, maxLength: 200000, rows: 24, hint: "Markdown." },
    { kind: "media", name: "cover_media_id", label: "Cover image", mediaKind: "image" },
  ];
}
