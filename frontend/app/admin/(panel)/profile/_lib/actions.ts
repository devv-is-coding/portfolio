"use server";

import { parseFields } from "@/lib/admin/fields";
import type { FormState } from "@/lib/admin/form-state";
import { adminDelete, adminWrite } from "@/lib/admin/save";
import { CACHE_TAGS } from "@/lib/api/cache-tags";
import type { components } from "@/lib/api/schema";
import { PROFILE_FIELDS, SOCIAL_LINK_FIELDS } from "./fields";

type Schemas = components["schemas"];
const TAGS = [CACHE_TAGS.profile];

/** Creates the profile on the first save, replaces it afterwards (the form sends every field). */
export async function saveProfile(_state: FormState, formData: FormData): Promise<FormState> {
  const body = parseFields(PROFILE_FIELDS, formData);
  return adminWrite({
    call: (api) => api.PUT("/admin/profile", { body: body as Schemas["ProfileWrite"] }),
    tags: TAGS,
    message: "Profile saved.",
  });
}

export async function saveSocialLink(id: number | null, _state: FormState, formData: FormData): Promise<FormState> {
  const body = parseFields(SOCIAL_LINK_FIELDS, formData);
  if (id === null) {
    return adminWrite({
      call: (api) => api.POST("/admin/profile/social-links", { body: body as Schemas["SocialLinkCreate"] }),
      tags: TAGS,
      message: "Link added.",
    });
  }
  return adminWrite({
    call: (api) =>
      api.PATCH("/admin/profile/social-links/{link_id}", {
        params: { path: { link_id: id } },
        body: body as Schemas["SocialLinkUpdate"],
      }),
    tags: TAGS,
  });
}

export async function deleteSocialLink(id: number): Promise<void> {
  await adminDelete({
    call: (api) => api.DELETE("/admin/profile/social-links/{link_id}", { params: { path: { link_id: id } } }),
    tags: TAGS,
  });
}
