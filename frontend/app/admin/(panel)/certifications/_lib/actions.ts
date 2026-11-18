"use server";

import { parseFields } from "@/lib/admin/fields";
import type { FormState } from "@/lib/admin/form-state";
import { adminDelete, adminWrite } from "@/lib/admin/save";
import { CACHE_TAGS } from "@/lib/api/cache-tags";
import type { components } from "@/lib/api/schema";
import { CERTIFICATIONS_FIELDS } from "./fields";

type Schemas = components["schemas"];
const TAGS = [CACHE_TAGS.certifications];

export async function saveCertification(id: number | null, _state: FormState, formData: FormData): Promise<FormState> {
  const body = parseFields(CERTIFICATIONS_FIELDS, formData);
  if (id === null) {
    return adminWrite({
      call: (api) => api.POST("/admin/certifications", { body: body as Schemas["CertificationCreate"] }),
      tags: TAGS,
      redirectTo: (item) => `/admin/certifications/${item.id}`,
    });
  }
  return adminWrite({
    call: (api) =>
      api.PATCH("/admin/certifications/{certification_id}", {
        params: { path: { certification_id: id } },
        body: body as Schemas["CertificationUpdate"],
      }),
    tags: TAGS,
  });
}

export async function deleteCertification(id: number): Promise<void> {
  await adminDelete({
    call: (api) => api.DELETE("/admin/certifications/{certification_id}", { params: { path: { certification_id: id } } }),
    tags: TAGS,
    redirectTo: "/admin/certifications",
  });
}
