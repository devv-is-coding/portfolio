import type { Metadata } from "next";
import { DataTable, PageHeader } from "@/components/admin/admin-ui";
import { ButtonLink } from "@/components/ui/button-link";
import { statusLabel } from "@/lib/admin/options";
import { asAdmin } from "@/lib/auth/session";
import { formatDate } from "@/lib/format";
import { ListPagination } from "@/components/admin/list-pagination";
import { ADMIN_PAGE_SIZE, keepPageInRange } from "@/lib/admin/list-pages";
import { pageParam } from "@/lib/search-params";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Projects" };

export default async function ProjectsAdminPage({ searchParams }: PageProps<"/admin/projects">) {
  const page = pageParam((await searchParams).page);
  const list = await asAdmin((api) =>
    api.GET("/admin/projects", { params: { query: { page, size: ADMIN_PAGE_SIZE, sort: "display_order" } } }),
  );
  keepPageInRange(list, "/admin/projects");
  const { items } = list;
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
      <ListPagination path="/admin/projects" list={list} />
    </>
  );
}
