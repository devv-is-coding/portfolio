import type { Metadata } from "next";
import { DataTable, PageHeader } from "@/components/admin/admin-ui";
import { ButtonLink } from "@/components/ui/button-link";
import { formatMonthYear } from "@/lib/format";
import { asAdmin } from "@/lib/auth/session";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Certifications" };

export default async function CertificationsAdminPage() {
  const { items } = await asAdmin((api) => api.GET("/certifications", { params: { query: { size: 100 } } }));
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
    </>
  );
}
