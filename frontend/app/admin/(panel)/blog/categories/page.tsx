import type { Metadata } from "next";
import { DataTable, PageHeader } from "@/components/admin/admin-ui";
import { ButtonLink } from "@/components/ui/button-link";
import { asAdmin } from "@/lib/auth/session";
import { ListPagination } from "@/components/admin/list-pagination";
import { ADMIN_PAGE_SIZE, keepPageInRange } from "@/lib/admin/list-pages";
import { pageParam } from "@/lib/search-params";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Categories" };

export default async function CategoriesAdminPage({ searchParams }: PageProps<"/admin/blog/categories">) {
  const page = pageParam((await searchParams).page);
  const list = await asAdmin((api) => api.GET("/blog/categories", { params: { query: { page, size: ADMIN_PAGE_SIZE } } }));
  keepPageInRange(list, "/admin/blog/categories");
  const { items } = list;
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
      <ListPagination path="/admin/blog/categories" list={list} />
      <p className="mt-6 text-sm text-muted">Deleting a category keeps its posts, uncategorized.</p>
    </>
  );
}
