"use server";

import { toMediaChoice, type MediaChoice } from "@/lib/admin/media-options";
import { ApiError } from "@/lib/api/errors";
import type { components } from "@/lib/api/schema";
import { asAdmin } from "@/lib/auth/session";

/** A signature for one browser upload to ImageKit (valid 30 minutes). */
export async function getUploadAuth(): Promise<components["schemas"]["UploadAuthResponse"]> {
  return asAdmin((api) => api.GET("/admin/media/upload-auth"));
}

export type RegisterResult = { ok: true; media: MediaChoice } | { ok: false; error: string };

/** Adds an uploaded file to the library; the API reads its type and size from ImageKit. */
export async function registerMedia(fileId: string, altText: string): Promise<RegisterResult> {
  try {
    const media = await asAdmin((api) =>
      api.POST("/admin/media", { body: { file_id: fileId, alt_text: altText.trim() || null } }),
    );
    return { ok: true, media: toMediaChoice(media) };
  } catch (error) {
    if (error instanceof ApiError) {
      return { ok: false, error: error.message };
    }
    throw error;
  }
}
