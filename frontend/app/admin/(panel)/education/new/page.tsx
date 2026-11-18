import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { ResourceForm } from "@/components/admin/resource-form";
import { saveSchool } from "../_lib/actions";
import { EDUCATION_FIELDS } from "../_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "New school" };

export default function NewSchoolPage() {
  return (
    <>
      <PageHeader eyebrow="Education" title="New school" back={{ href: "/admin/education", label: "All education" }} />
      <ResourceForm fields={EDUCATION_FIELDS} action={saveSchool.bind(null, null)} submitLabel="Create school" />
    </>
  );
}
