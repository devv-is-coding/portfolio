"use server";

import { parseFields } from "@/lib/admin/fields";
import type { FormState } from "@/lib/admin/form-state";
import { adminDelete, adminWrite } from "@/lib/admin/save";
import { CACHE_TAGS } from "@/lib/api/cache-tags";
import type { components } from "@/lib/api/schema";
import { TAGS_FIELDS } from "./fields";

type Schemas = components["schemas"];
const TAGS = [CACHE_TAGS.blog];

export async function saveTag(id: number | null, _state: FormState, formData: FormData): Promise<FormState> {
  const body = parseFields(TAGS_FIELDS, formData);
  if (id === null) {
    return adminWrite({
      call: (api) => api.POST("/admin/blog/tags", { body: body as Schemas["BlogTermCreate"] }),
      tags: TAGS,
      redirectTo: (item) => `/admin/blog/tags/${item.id}`,
    });
  }
  return adminWrite({
    call: (api) =>
      api.PATCH("/admin/blog/tags/{tag_id}", {
        params: { path: { tag_id: id } },
        body: body as Schemas["BlogTermUpdate"],
      }),
    tags: TAGS,
  });
}

export async function deleteTag(id: number): Promise<void> {
  await adminDelete({
    call: (api) => api.DELETE("/admin/blog/tags/{tag_id}", { params: { path: { tag_id: id } } }),
    tags: TAGS,
    redirectTo: "/admin/blog/tags",
  });
}
