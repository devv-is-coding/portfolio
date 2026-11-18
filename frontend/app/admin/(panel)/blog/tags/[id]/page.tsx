import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { DeleteButton } from "@/components/admin/delete-button";
import { ResourceForm } from "@/components/admin/resource-form";
import { adminItem, idParam } from "@/lib/admin/reads";
import { deleteTag, saveTag } from "../_lib/actions";
import { TAGS_FIELDS } from "../_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Edit tag" };

export default async function EditTagPage({ params }: PageProps<"/admin/blog/tags/[id]">) {
  const id = idParam((await params).id);
  const item = await adminItem((api) => api.GET("/admin/blog/tags/{tag_id}", { params: { path: { tag_id: id } } }));
  return (
    <>
      <PageHeader
        eyebrow="Tags"
        title={item.name}
        back={{ href: "/admin/blog/tags", label: "All tags" }}
        action={<DeleteButton action={deleteTag.bind(null, id)} what={`the tag ${item.name}`} />}
      />
      <ResourceForm fields={TAGS_FIELDS} action={saveTag.bind(null, id)} values={item} />
    </>
  );
}
