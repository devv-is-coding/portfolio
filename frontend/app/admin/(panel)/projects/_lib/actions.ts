"use server";

import { parseFields } from "@/lib/admin/fields";
import type { FormState } from "@/lib/admin/form-state";
import { adminDelete, adminWrite } from "@/lib/admin/save";
import { CACHE_TAGS } from "@/lib/api/cache-tags";
import type { components } from "@/lib/api/schema";
import { IMAGE_ADD_FIELDS, IMAGE_EDIT_FIELDS, PROJECT_FIELDS } from "./fields";

type Schemas = components["schemas"];
const TAGS = [CACHE_TAGS.projects];

export async function saveProject(id: number | null, _state: FormState, formData: FormData): Promise<FormState> {
  const body = parseFields(PROJECT_FIELDS, formData);
  if (id === null) {
    return adminWrite({
      call: (api) => api.POST("/admin/projects", { body: body as Schemas["ProjectCreate"] }),
      tags: TAGS,
      redirectTo: (project) => `/admin/projects/${project.id}`,
    });
  }
  return adminWrite({
    call: (api) =>
      api.PATCH("/admin/projects/{project_id}", {
        params: { path: { project_id: id } },
        body: body as Schemas["ProjectUpdate"],
      }),
    tags: TAGS,
  });
}

export async function deleteProject(id: number): Promise<void> {
  await adminDelete({
    call: (api) => api.DELETE("/admin/projects/{project_id}", { params: { path: { project_id: id } } }),
    tags: TAGS,
    redirectTo: "/admin/projects",
  });
}

/** Replaces the project's skills with the checked ones. */
export async function saveProjectSkills(id: number, _state: FormState, formData: FormData): Promise<FormState> {
  const skillIds = formData.getAll("ids").map(Number);
  return adminWrite({
    call: (api) =>
      api.PUT("/admin/projects/{project_id}/skills", {
        params: { path: { project_id: id } },
        body: { skill_ids: skillIds },
      }),
    tags: TAGS,
    message: "Skills saved.",
  });
}

export async function addProjectImage(id: number, _state: FormState, formData: FormData): Promise<FormState> {
  const body = parseFields(IMAGE_ADD_FIELDS, formData);
  return adminWrite({
    call: (api) =>
      api.POST("/admin/projects/{project_id}/images", {
        params: { path: { project_id: id } },
        body: body as Schemas["ProjectImageCreate"],
      }),
    tags: TAGS,
    message: "Image added.",
  });
}

export async function saveProjectImage(
  projectId: number,
  imageId: number,
  _state: FormState,
  formData: FormData,
): Promise<FormState> {
  const body = parseFields(IMAGE_EDIT_FIELDS, formData);
  return adminWrite({
    call: (api) =>
      api.PATCH("/admin/projects/{project_id}/images/{image_id}", {
        params: { path: { project_id: projectId, image_id: imageId } },
        body: body as Schemas["ProjectImageUpdate"],
      }),
    tags: TAGS,
  });
}

export async function deleteProjectImage(projectId: number, imageId: number): Promise<void> {
  await adminDelete({
    call: (api) =>
      api.DELETE("/admin/projects/{project_id}/images/{image_id}", {
        params: { path: { project_id: projectId, image_id: imageId } },
      }),
    tags: TAGS,
  });
}
