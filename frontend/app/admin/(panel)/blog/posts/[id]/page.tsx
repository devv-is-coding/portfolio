import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { ChecklistForm } from "@/components/admin/checklist-form";
import { DeleteButton } from "@/components/admin/delete-button";
import { ResourceForm } from "@/components/admin/resource-form";
import { mediaOptions } from "@/lib/admin/media-options";
import { adminItem, getCategoriesForAdmin, getTagsForAdmin, idParam } from "@/lib/admin/reads";
import { deletePost, savePost, savePostTags } from "../_lib/actions";
import { postFields } from "../_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Edit post" };

export default async function EditPostPage({ params }: PageProps<"/admin/blog/posts/[id]">) {
  const id = idParam((await params).id);
  const [post, categories, tags, media] = await Promise.all([
    adminItem((api) => api.GET("/admin/blog/posts/{post_id}", { params: { path: { post_id: id } } })),
    getCategoriesForAdmin(),
    getTagsForAdmin(),
    mediaOptions(),
  ]);

  return (
    <>
      <PageHeader
        eyebrow="Blog"
        title={post.title}
        back={{ href: "/admin/blog/posts", label: "All posts" }}
        action={<DeleteButton action={deletePost.bind(null, id)} what={`the post ${post.title}`} />}
      />
      <ResourceForm fields={postFields(categories)} action={savePost.bind(null, id)} values={post} media={media} />
      <section className="mt-16 flex flex-col gap-6 border-t border-line pt-10" aria-labelledby="tags-heading">
        <h2 id="tags-heading" className="font-display text-2xl">
          Tags
        </h2>
        <ChecklistForm
          legend="Tags of this post"
          options={tags.map((tag) => ({ id: tag.id, label: tag.name }))}
          selected={post.tags.map((tag) => tag.id)}
          action={savePostTags.bind(null, id)}
          submitLabel="Save tags"
          empty="No tags yet: add them under Blog tags first."
        />
      </section>
    </>
  );
}
