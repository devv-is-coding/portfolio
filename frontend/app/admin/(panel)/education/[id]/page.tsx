import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { DeleteButton } from "@/components/admin/delete-button";
import { ResourceForm } from "@/components/admin/resource-form";
import { adminItem, idParam } from "@/lib/admin/reads";
import { deleteSchool, saveSchool } from "../_lib/actions";
import { EDUCATION_FIELDS } from "../_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Edit school" };

export default async function EditSchoolPage({ params }: PageProps<"/admin/education/[id]">) {
  const id = idParam((await params).id);
  const item = await adminItem((api) => api.GET("/admin/education/{education_id}", { params: { path: { education_id: id } } }));
  return (
    <>
      <PageHeader
        eyebrow="Education"
        title={item.institution}
        back={{ href: "/admin/education", label: "All education" }}
        action={<DeleteButton action={deleteSchool.bind(null, id)} what={`the school ${item.institution}`} />}
      />
      <ResourceForm fields={EDUCATION_FIELDS} action={saveSchool.bind(null, id)} values={item} />
    </>
  );
}
