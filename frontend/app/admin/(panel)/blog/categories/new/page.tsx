import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { ResourceForm } from "@/components/admin/resource-form";
import { saveCategory } from "../_lib/actions";
import { CATEGORIES_FIELDS } from "../_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "New category" };

export default function NewCategoryPage() {
  return (
    <>
      <PageHeader eyebrow="Categories" title="New category" back={{ href: "/admin/blog/categories", label: "All categories" }} />
      <ResourceForm fields={CATEGORIES_FIELDS} action={saveCategory.bind(null, null)} submitLabel="Create category" />
    </>
  );
}
