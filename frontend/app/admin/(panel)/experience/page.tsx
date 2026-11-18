import type { Metadata } from "next";
import { DataTable, PageHeader } from "@/components/admin/admin-ui";
import { ButtonLink } from "@/components/ui/button-link";
import { formatPeriod } from "@/lib/format";
import { asAdmin } from "@/lib/auth/session";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Experience" };

export default async function ExperienceAdminPage() {
  const { items } = await asAdmin((api) => api.GET("/experiences", { params: { query: { size: 100 } } }));
  return (
    <>
      <PageHeader
        eyebrow="Content"
        title="Experience"
        action={
          <ButtonLink href="/admin/experience/new" size="sm">
            New job
          </ButtonLink>
        }
      />
      <DataTable
        items={items}
        href={(item) => `/admin/experience/${item.id}`}
        empty="No experience yet"
        columns={[
          { label: "Position", value: (item) => item.position },
          { label: "Company", value: (item) => item.company },
          { label: "Period", value: (item) => formatPeriod(item.start_date, item.end_date) },
        ]}
      />
    </>
  );
}
