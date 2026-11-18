import type { Metadata } from "next";
import { DataTable, PageHeader } from "@/components/admin/admin-ui";
import { ButtonLink } from "@/components/ui/button-link";
import { asAdmin } from "@/lib/auth/session";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Tags" };

export default async function TagsAdminPage() {
  const { items } = await asAdmin((api) => api.GET("/blog/tags", { params: { query: { size: 100 } } }));
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
      <p className="mt-6 text-sm text-muted">Deleting a tag removes it from its posts.</p>
    </>
  );
}
