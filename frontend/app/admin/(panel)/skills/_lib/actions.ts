"use server";

import { adminDelete, adminWrite } from "@/lib/admin/save";
import { parseFields } from "@/lib/admin/fields";
import type { FormState } from "@/lib/admin/form-state";
import { CACHE_TAGS } from "@/lib/api/cache-tags";
import type { components } from "@/lib/api/schema";
import { SKILL_FIELDS } from "./fields";

type Schemas = components["schemas"];
// Projects show their skills, so a skill change refreshes them too.
const TAGS = [CACHE_TAGS.skills, CACHE_TAGS.projects];

export async function saveSkill(id: number | null, _state: FormState, formData: FormData): Promise<FormState> {
  const body = parseFields(SKILL_FIELDS, formData);
  if (id === null) {
    return adminWrite({
      call: (api) => api.POST("/admin/skills", { body: body as Schemas["SkillCreate"] }),
      tags: TAGS,
      redirectTo: (skill) => `/admin/skills/${skill.id}`,
    });
  }
  return adminWrite({
    call: (api) =>
      api.PATCH("/admin/skills/{skill_id}", { params: { path: { skill_id: id } }, body: body as Schemas["SkillUpdate"] }),
    tags: TAGS,
  });
}

export async function deleteSkill(id: number): Promise<void> {
  await adminDelete({
    call: (api) => api.DELETE("/admin/skills/{skill_id}", { params: { path: { skill_id: id } } }),
    tags: TAGS,
    redirectTo: "/admin/skills",
  });
}
