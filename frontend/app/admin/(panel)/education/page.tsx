import type { Metadata } from "next";
import { DataTable, PageHeader } from "@/components/admin/admin-ui";
import { ButtonLink } from "@/components/ui/button-link";
import { formatPeriod } from "@/lib/format";
import { asAdmin } from "@/lib/auth/session";
import { ListPagination } from "@/components/admin/list-pagination";
import { ADMIN_PAGE_SIZE, keepPageInRange } from "@/lib/admin/list-pages";
import { pageParam } from "@/lib/search-params";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Education" };

export default async function EducationAdminPage({ searchParams }: PageProps<"/admin/education">) {
  const page = pageParam((await searchParams).page);
  const list = await asAdmin((api) => api.GET("/education", { params: { query: { page, size: ADMIN_PAGE_SIZE } } }));
  keepPageInRange(list, "/admin/education");
  const { items } = list;
  return (
    <>
      <PageHeader
        eyebrow="Content"
        title="Education"
        action={
          <ButtonLink href="/admin/education/new" size="sm">
            New school
          </ButtonLink>
        }
      />
      <DataTable
        items={items}
        href={(item) => `/admin/education/${item.id}`}
        empty="No education yet"
        columns={[
          { label: "Institution", value: (item) => item.institution },
          { label: "Degree", value: (item) => item.degree ?? "—" },
          { label: "Period", value: (item) => formatPeriod(item.start_date, item.end_date, "In progress") },
        ]}
      />
      <ListPagination path="/admin/education" list={list} />
    </>
  );
}
