import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { ResourceForm } from "@/components/admin/resource-form";
import { saveJob } from "../_lib/actions";
import { EXPERIENCE_FIELDS } from "../_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "New job" };

export default function NewJobPage() {
  return (
    <>
      <PageHeader eyebrow="Experience" title="New job" back={{ href: "/admin/experience", label: "All experience" }} />
      <ResourceForm fields={EXPERIENCE_FIELDS} action={saveJob.bind(null, null)} submitLabel="Create job" />
    </>
  );
}
