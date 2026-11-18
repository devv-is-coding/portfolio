"use server";

import { parseFields } from "@/lib/admin/fields";
import type { FormState } from "@/lib/admin/form-state";
import { adminDelete, adminWrite } from "@/lib/admin/save";
import { CACHE_TAGS } from "@/lib/api/cache-tags";
import { ApiError } from "@/lib/api/errors";
import type { components } from "@/lib/api/schema";
import { asAdmin } from "@/lib/auth/session";
import { MEDIA_FIELDS } from "./fields";

type Schemas = components["schemas"];
// Media shows up anywhere (avatar, thumbnails, covers, icons): a change refreshes every page.
const ALL_TAGS = Object.values(CACHE_TAGS);

/** A signature for one browser upload to ImageKit (valid 30 minutes). */
export async function getUploadAuth(): Promise<Schemas["UploadAuthResponse"]> {
  return asAdmin((api) => api.GET("/admin/media/upload-auth"));
}

export type RegisterResult = { ok: true } | { ok: false; error: string };

/** Adds an uploaded file to the library; the API reads its type and size from ImageKit. */
export async function registerMedia(fileId: string, altText: string): Promise<RegisterResult> {
  try {
    await asAdmin((api) =>
      api.POST("/admin/media", { body: { file_id: fileId, alt_text: altText.trim() || null } }),
    );
  } catch (error) {
    if (error instanceof ApiError) {
      return { ok: false, error: error.message };
    }
    throw error;
  }
  return { ok: true };
}

export async function saveMediaAlt(id: number, _state: FormState, formData: FormData): Promise<FormState> {
  const body = parseFields(MEDIA_FIELDS, formData);
  return adminWrite({
    call: (api) =>
      api.PATCH("/admin/media/{media_id}", { params: { path: { media_id: id } }, body: body as Schemas["MediaUpdate"] }),
    tags: ALL_TAGS,
  });
}

/** Deletes the file: pages that used it lose that image; ImageKit removes it in the background. */
export async function deleteMedia(id: number): Promise<void> {
  await adminDelete({
    call: (api) => api.DELETE("/admin/media/{media_id}", { params: { path: { media_id: id } } }),
    tags: ALL_TAGS,
  });
}
