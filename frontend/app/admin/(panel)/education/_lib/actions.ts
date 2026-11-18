"use server";

import { parseFields } from "@/lib/admin/fields";
import type { FormState } from "@/lib/admin/form-state";
import { adminDelete, adminWrite } from "@/lib/admin/save";
import { CACHE_TAGS } from "@/lib/api/cache-tags";
import type { components } from "@/lib/api/schema";
import { EDUCATION_FIELDS } from "./fields";

type Schemas = components["schemas"];
const TAGS = [CACHE_TAGS.education];

export async function saveSchool(id: number | null, _state: FormState, formData: FormData): Promise<FormState> {
  const body = parseFields(EDUCATION_FIELDS, formData);
  if (id === null) {
    return adminWrite({
      call: (api) => api.POST("/admin/education", { body: body as Schemas["EducationCreate"] }),
      tags: TAGS,
      redirectTo: (item) => `/admin/education/${item.id}`,
    });
  }
  return adminWrite({
    call: (api) =>
      api.PATCH("/admin/education/{education_id}", {
        params: { path: { education_id: id } },
        body: body as Schemas["EducationUpdate"],
      }),
    tags: TAGS,
  });
}

export async function deleteSchool(id: number): Promise<void> {
  await adminDelete({
    call: (api) => api.DELETE("/admin/education/{education_id}", { params: { path: { education_id: id } } }),
    tags: TAGS,
    redirectTo: "/admin/education",
  });
}
