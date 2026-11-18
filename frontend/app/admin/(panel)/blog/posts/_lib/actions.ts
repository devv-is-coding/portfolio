"use server";

import { parseFields } from "@/lib/admin/fields";
import type { FormState } from "@/lib/admin/form-state";
import { adminDelete, adminWrite } from "@/lib/admin/save";
import { CACHE_TAGS } from "@/lib/api/cache-tags";
import type { components } from "@/lib/api/schema";
import { postFields } from "./fields";

type Schemas = components["schemas"];
const TAGS = [CACHE_TAGS.blog];

export async function savePost(id: number | null, _state: FormState, formData: FormData): Promise<FormState> {
  const body = parseFields(postFields(), formData);
  // The category select sends its id as text.
  body.category_id = body.category_id === null ? null : Number(body.category_id);
  if (id === null) {
    return adminWrite({
      call: (api) => api.POST("/admin/blog/posts", { body: body as Schemas["BlogPostCreate"] }),
      tags: TAGS,
      redirectTo: (post) => `/admin/blog/posts/${post.id}`,
    });
  }
  return adminWrite({
    call: (api) =>
      api.PATCH("/admin/blog/posts/{post_id}", {
        params: { path: { post_id: id } },
        body: body as Schemas["BlogPostUpdate"],
      }),
    tags: TAGS,
  });
}

export async function deletePost(id: number): Promise<void> {
  await adminDelete({
    call: (api) => api.DELETE("/admin/blog/posts/{post_id}", { params: { path: { post_id: id } } }),
    tags: TAGS,
    redirectTo: "/admin/blog/posts",
  });
}

/** Replaces the post's tags with the checked ones. */
export async function savePostTags(id: number, _state: FormState, formData: FormData): Promise<FormState> {
  return adminWrite({
    call: (api) =>
      api.PUT("/admin/blog/posts/{post_id}/tags", {
        params: { path: { post_id: id } },
        body: { tag_ids: formData.getAll("ids").map(Number) },
      }),
    tags: TAGS,
    message: "Tags saved.",
  });
}
