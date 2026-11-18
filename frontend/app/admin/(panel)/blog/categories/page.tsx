import type { Metadata } from "next";
import { DataTable, PageHeader } from "@/components/admin/admin-ui";
import { ButtonLink } from "@/components/ui/button-link";
import { asAdmin } from "@/lib/auth/session";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Categories" };

export default async function CategoriesAdminPage() {
  const { items } = await asAdmin((api) => api.GET("/blog/categories", { params: { query: { size: 100 } } }));
  return (
    <>
      <PageHeader
        eyebrow="Content"
        title="Categories"
        action={
          <ButtonLink href="/admin/blog/categories/new" size="sm">
            New category
          </ButtonLink>
        }
      />
      <DataTable
        items={items}
        href={(item) => `/admin/blog/categories/${item.id}`}
        empty="No categories yet"
        columns={[
          { label: "Name", value: (item) => item.name },
          { label: "Slug", value: (item) => item.slug },
        ]}
      />
      <p className="mt-6 text-sm text-muted">Deleting a category keeps its posts, uncategorized.</p>
    </>
  );
}
