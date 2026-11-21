import type { Metadata } from "next";
import { DataTable, PageHeader } from "@/components/admin/admin-ui";
import { ButtonLink } from "@/components/ui/button-link";
import { asAdmin } from "@/lib/auth/session";
import { ListPagination } from "@/components/admin/list-pagination";
import { ADMIN_PAGE_SIZE, keepPageInRange } from "@/lib/admin/list-pages";
import { pageParam } from "@/lib/search-params";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Tags" };

export default async function TagsAdminPage({ searchParams }: PageProps<"/admin/blog/tags">) {
  const page = pageParam((await searchParams).page);
  const list = await asAdmin((api) => api.GET("/blog/tags", { params: { query: { page, size: ADMIN_PAGE_SIZE } } }));
  keepPageInRange(list, "/admin/blog/tags");
  const { items } = list;
  return (
    <>
      <PageHeader
        eyebrow="Content"
        title="Tags"
        action={
          <ButtonLink href="/admin/blog/tags/new" size="sm">
            New tag
          </ButtonLink>
        }
      />
      <DataTable
        items={items}
        href={(item) => `/admin/blog/tags/${item.id}`}
        empty="No tags yet"
        columns={[
          { label: "Name", value: (item) => item.name },
          { label: "Slug", value: (item) => item.slug },
        ]}
      />
      <ListPagination path="/admin/blog/tags" list={list} />
      <p className="mt-6 text-sm text-muted">Deleting a tag removes it from its posts.</p>
    </>
  );
}
