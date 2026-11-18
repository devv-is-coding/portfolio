import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { DeleteButton } from "@/components/admin/delete-button";
import { ResourceForm } from "@/components/admin/resource-form";
import { adminItem, idParam } from "@/lib/admin/reads";
import { deleteCategory, saveCategory } from "../_lib/actions";
import { CATEGORIES_FIELDS } from "../_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Edit category" };

export default async function EditCategoryPage({ params }: PageProps<"/admin/blog/categories/[id]">) {
  const id = idParam((await params).id);
  const item = await adminItem((api) => api.GET("/admin/blog/categories/{category_id}", { params: { path: { category_id: id } } }));
  return (
    <>
      <PageHeader
        eyebrow="Categories"
        title={item.name}
        back={{ href: "/admin/blog/categories", label: "All categories" }}
        action={<DeleteButton action={deleteCategory.bind(null, id)} what={`the category ${item.name}`} />}
      />
      <ResourceForm fields={CATEGORIES_FIELDS} action={saveCategory.bind(null, id)} values={item} />
    </>
  );
}
