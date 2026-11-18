import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { ResourceForm } from "@/components/admin/resource-form";
import { saveCertification } from "../_lib/actions";
import { CERTIFICATIONS_FIELDS } from "../_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "New certification" };

export default function NewCertificationPage() {
  return (
    <>
      <PageHeader eyebrow="Certifications" title="New certification" back={{ href: "/admin/certifications", label: "All certifications" }} />
      <ResourceForm fields={CERTIFICATIONS_FIELDS} action={saveCertification.bind(null, null)} submitLabel="Create certification" />
    </>
  );
}
