import type { Metadata } from "next";
import { ButtonLink } from "@/components/ui/button-link";
import { DataTable, PageHeader } from "@/components/admin/admin-ui";
import { ListPagination } from "@/components/admin/list-pagination";
import { ADMIN_PAGE_SIZE, keepPageInRange } from "@/lib/admin/list-pages";
import { asAdmin } from "@/lib/auth/session";
import { pageParam } from "@/lib/search-params";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Skills" };

export default async function SkillsPage({ searchParams }: PageProps<"/admin/skills">) {
  const page = pageParam((await searchParams).page);
  const list = await asAdmin((api) => api.GET("/skills", { params: { query: { page, size: ADMIN_PAGE_SIZE } } }));
  keepPageInRange(list, "/admin/skills");
  return (
    <>
      <PageHeader
        eyebrow="Content"
        title="Skills"
        action={
          <ButtonLink href="/admin/skills/new" size="sm">
            New skill
          </ButtonLink>
        }
      />
      <DataTable
        items={list.items}
        href={(skill) => `/admin/skills/${skill.id}`}
        empty="No skills yet"
        columns={[
          { label: "Name", value: (skill) => skill.name },
          { label: "Category", value: (skill) => skill.category ?? "—" },
          { label: "Order", value: (skill) => skill.display_order },
        ]}
      />
      <ListPagination path="/admin/skills" list={list} />
    </>
  );
}
