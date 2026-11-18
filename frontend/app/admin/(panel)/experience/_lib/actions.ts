"use server";

import { parseFields } from "@/lib/admin/fields";
import type { FormState } from "@/lib/admin/form-state";
import { adminDelete, adminWrite } from "@/lib/admin/save";
import { CACHE_TAGS } from "@/lib/api/cache-tags";
import type { components } from "@/lib/api/schema";
import { EXPERIENCE_FIELDS } from "./fields";

type Schemas = components["schemas"];
const TAGS = [CACHE_TAGS.experiences];

export async function saveJob(id: number | null, _state: FormState, formData: FormData): Promise<FormState> {
  const body = parseFields(EXPERIENCE_FIELDS, formData);
  if (id === null) {
    return adminWrite({
      call: (api) => api.POST("/admin/experiences", { body: body as Schemas["ExperienceCreate"] }),
      tags: TAGS,
      redirectTo: (item) => `/admin/experience/${item.id}`,
    });
  }
  return adminWrite({
    call: (api) =>
      api.PATCH("/admin/experiences/{experience_id}", {
        params: { path: { experience_id: id } },
        body: body as Schemas["ExperienceUpdate"],
      }),
    tags: TAGS,
  });
}

export async function deleteJob(id: number): Promise<void> {
  await adminDelete({
    call: (api) => api.DELETE("/admin/experiences/{experience_id}", { params: { path: { experience_id: id } } }),
    tags: TAGS,
    redirectTo: "/admin/experience",
  });
}
