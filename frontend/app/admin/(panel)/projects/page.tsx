import type { Metadata } from "next";
import { DataTable, PageHeader } from "@/components/admin/admin-ui";
import { ButtonLink } from "@/components/ui/button-link";
import { statusLabel } from "@/lib/admin/options";
import { asAdmin } from "@/lib/auth/session";
import { formatDate } from "@/lib/format";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Projects" };

export default async function ProjectsAdminPage() {
  const { items, total } = await asAdmin((api) =>
    api.GET("/admin/projects", { params: { query: { size: 100, sort: "display_order" } } }),
  );
  return (
    <>
      <PageHeader
        eyebrow="Content"
        title="Projects"
        action={
          <ButtonLink href="/admin/projects/new" size="sm">
            New project
          </ButtonLink>
        }
      />
      <DataTable
        items={items}
        href={(project) => `/admin/projects/${project.id}`}
        empty="No projects yet"
        columns={[
          { label: "Title", value: (project) => project.title },
          { label: "Status", value: (project) => statusLabel(project.status) },
          { label: "Featured", value: (project) => (project.is_featured ? "Yes" : "—") },
          { label: "Published", value: (project) => (project.published_at ? formatDate(project.published_at) : "—") },
          { label: "Order", value: (project) => project.display_order },
        ]}
      />
      {total > items.length && <p className="mt-6 text-sm text-muted">Showing the first {items.length} of {total}.</p>}
    </>
  );
}
