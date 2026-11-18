import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { ResourceForm } from "@/components/admin/resource-form";
import { saveTag } from "../_lib/actions";
import { TAGS_FIELDS } from "../_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "New tag" };

export default function NewTagPage() {
  return (
    <>
      <PageHeader eyebrow="Tags" title="New tag" back={{ href: "/admin/blog/tags", label: "All tags" }} />
      <ResourceForm fields={TAGS_FIELDS} action={saveTag.bind(null, null)} submitLabel="Create tag" />
    </>
  );
}
