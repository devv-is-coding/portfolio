import type { Metadata } from "next";
import { DataTable, PageHeader } from "@/components/admin/admin-ui";
import { ButtonLink } from "@/components/ui/button-link";
import { formatMonthYear } from "@/lib/format";
import { asAdmin } from "@/lib/auth/session";
import { ListPagination } from "@/components/admin/list-pagination";
import { ADMIN_PAGE_SIZE, keepPageInRange } from "@/lib/admin/list-pages";
import { pageParam } from "@/lib/search-params";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Certifications" };

export default async function CertificationsAdminPage({ searchParams }: PageProps<"/admin/certifications">) {
  const page = pageParam((await searchParams).page);
  const list = await asAdmin((api) => api.GET("/certifications", { params: { query: { page, size: ADMIN_PAGE_SIZE } } }));
  keepPageInRange(list, "/admin/certifications");
  const { items } = list;
  return (
    <>
      <PageHeader
        eyebrow="Content"
        title="Certifications"
        action={
          <ButtonLink href="/admin/certifications/new" size="sm">
            New certification
          </ButtonLink>
        }
      />
      <DataTable
        items={items}
        href={(item) => `/admin/certifications/${item.id}`}
        empty="No certifications yet"
        columns={[
          { label: "Name", value: (item) => item.name },
          { label: "Issuer", value: (item) => item.issuing_organization },
          { label: "Issued", value: (item) => item.issued_at ? formatMonthYear(item.issued_at) : "—" },
        ]}
      />
      <ListPagination path="/admin/certifications" list={list} />
    </>
  );
}
