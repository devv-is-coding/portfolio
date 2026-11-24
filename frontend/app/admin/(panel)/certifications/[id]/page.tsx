import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { DeleteButton } from "@/components/admin/delete-button";
import { ResourceForm } from "@/components/admin/resource-form";
import { mediaOptions } from "@/lib/admin/media-options";
import { adminItem, idParam } from "@/lib/admin/reads";
import { deleteCertification, saveCertification } from "../_lib/actions";
import { CERTIFICATIONS_FIELDS } from "../_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Edit certification" };

export default async function EditCertificationPage({ params }: PageProps<"/admin/certifications/[id]">) {
  const id = idParam((await params).id);
  const [item, media] = await Promise.all([
    adminItem((api) => api.GET("/admin/certifications/{certification_id}", { params: { path: { certification_id: id } } })),
    mediaOptions(),
  ]);
  return (
    <>
      <PageHeader
        eyebrow="Certifications"
        title={item.name}
        back={{ href: "/admin/certifications", label: "All certifications" }}
        action={<DeleteButton action={deleteCertification.bind(null, id)} what={`the certification ${item.name}`} />}
      />
      <ResourceForm fields={CERTIFICATIONS_FIELDS} action={saveCertification.bind(null, id)} values={item} media={media} />
    </>
  );
}
