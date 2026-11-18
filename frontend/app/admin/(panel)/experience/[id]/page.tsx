import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { DeleteButton } from "@/components/admin/delete-button";
import { ResourceForm } from "@/components/admin/resource-form";
import { adminItem, idParam } from "@/lib/admin/reads";
import { deleteJob, saveJob } from "../_lib/actions";
import { EXPERIENCE_FIELDS } from "../_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Edit job" };

export default async function EditJobPage({ params }: PageProps<"/admin/experience/[id]">) {
  const id = idParam((await params).id);
  const item = await adminItem((api) => api.GET("/admin/experiences/{experience_id}", { params: { path: { experience_id: id } } }));
  return (
    <>
      <PageHeader
        eyebrow="Experience"
        title={item.position}
        back={{ href: "/admin/experience", label: "All experience" }}
        action={<DeleteButton action={deleteJob.bind(null, id)} what={`the job ${item.position}`} />}
      />
      <ResourceForm fields={EXPERIENCE_FIELDS} action={saveJob.bind(null, id)} values={item} />
    </>
  );
}
