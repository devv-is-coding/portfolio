"use server";

import { refresh, updateTag } from "next/cache";
import { parseFields } from "@/lib/admin/fields";
import type { FormState } from "@/lib/admin/form-state";
import { adminDelete, adminWrite } from "@/lib/admin/save";
import { CACHE_TAGS } from "@/lib/api/cache-tags";
import { ApiError } from "@/lib/api/errors";
import type { components } from "@/lib/api/schema";
import { asAdmin } from "@/lib/auth/session";
import { IMAGE_EDIT_FIELDS, PROJECT_FIELDS } from "./fields";

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

const pictures = (count: number) => (count === 1 ? "1 picture" : `${count} pictures`);

/**
 * Adds the ticked pictures (`ids`) to the end of the gallery, in the order shown: one API call
 * each, one after the other, so their display order follows `firstOrder`. Pictures the API
 * refuses are reported; the others are still added.
 */
export async function addProjectImages(
  id: number,
  firstOrder: number,
  _state: FormState,
  formData: FormData,
): Promise<FormState> {
  const mediaIds = formData.getAll("ids").map(Number).filter((mediaId) => Number.isInteger(mediaId) && mediaId > 0);
  if (mediaIds.length === 0) {
    return { status: "failed", error: "Tick at least one picture first.", fieldErrors: {} };
  }
  const errors: string[] = [];
  for (const [index, mediaId] of mediaIds.entries()) {
    try {
      await asAdmin((api) =>
        api.POST("/admin/projects/{project_id}/images", {
          params: { path: { project_id: id } },
          body: { media_id: mediaId, display_order: firstOrder + index },
        }),
      );
    } catch (error) {
      if (!(error instanceof ApiError)) {
        throw error;
      }
      errors.push(error.message);
    }
  }
  const added = mediaIds.length - errors.length;
  if (added > 0) {
    for (const tag of TAGS) {
      updateTag(tag);
    }
    refresh();
  }
  if (errors.length === 0) {
    return { status: "saved", message: `${pictures(added)} added to the gallery.` };
  }
  const reasons = [...new Set(errors)].join(" ");
  return {
    status: "failed",
    error: added > 0 ? `${pictures(added)} added; ${pictures(errors.length)} couldn't be: ${reasons}` : `Nothing was added: ${reasons}`,
    fieldErrors: {},
  };
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
