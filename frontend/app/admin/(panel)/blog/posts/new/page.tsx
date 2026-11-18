import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { ResourceForm } from "@/components/admin/resource-form";
import { mediaOptions } from "@/lib/admin/media-options";
import { getCategoriesForAdmin } from "@/lib/admin/reads";
import { savePost } from "../_lib/actions";
import { postFields } from "../_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "New post" };

export default async function NewPostPage() {
  const [categories, media] = await Promise.all([getCategoriesForAdmin(), mediaOptions()]);
  return (
    <>
      <PageHeader eyebrow="Blog" title="New post" back={{ href: "/admin/blog/posts", label: "All posts" }} />
      <ResourceForm
        fields={postFields(categories)}
        action={savePost.bind(null, null)}
        values={{ status: "draft" }}
        media={media}
        submitLabel="Create post"
      />
    </>
  );
}
