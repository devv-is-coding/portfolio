"use server";

import { parseFields } from "@/lib/admin/fields";
import type { FormState } from "@/lib/admin/form-state";
import { adminDelete, adminWrite } from "@/lib/admin/save";
import { CACHE_TAGS } from "@/lib/api/cache-tags";
import type { components } from "@/lib/api/schema";
import { CATEGORIES_FIELDS } from "./fields";

type Schemas = components["schemas"];
const TAGS = [CACHE_TAGS.blog];

export async function saveCategory(id: number | null, _state: FormState, formData: FormData): Promise<FormState> {
  const body = parseFields(CATEGORIES_FIELDS, formData);
  if (id === null) {
    return adminWrite({
      call: (api) => api.POST("/admin/blog/categories", { body: body as Schemas["BlogTermCreate"] }),
      tags: TAGS,
      redirectTo: (item) => `/admin/blog/categories/${item.id}`,
    });
  }
  return adminWrite({
    call: (api) =>
      api.PATCH("/admin/blog/categories/{category_id}", {
        params: { path: { category_id: id } },
        body: body as Schemas["BlogTermUpdate"],
      }),
    tags: TAGS,
  });
}

export async function deleteCategory(id: number): Promise<void> {
  await adminDelete({
    call: (api) => api.DELETE("/admin/blog/categories/{category_id}", { params: { path: { category_id: id } } }),
    tags: TAGS,
    redirectTo: "/admin/blog/categories",
  });
}
