import type { Metadata } from "next";
import { DataTable, PageHeader } from "@/components/admin/admin-ui";
import { ButtonLink } from "@/components/ui/button-link";
import { formatPeriod } from "@/lib/format";
import { asAdmin } from "@/lib/auth/session";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Education" };

export default async function EducationAdminPage() {
  const { items } = await asAdmin((api) => api.GET("/education", { params: { query: { size: 100 } } }));
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
    </>
  );
}
