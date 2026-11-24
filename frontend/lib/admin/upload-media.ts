import { getUploadAuth, registerMedia, type RegisterResult } from "@/lib/admin/media-actions";

/**
 * Uploads one file straight from the browser to ImageKit with its own signature from the API
 * (ImageKit accepts each signature once; the file never passes through this server), then
 * registers it in the media library.
 */
export async function uploadMedia(file: File, altText: string): Promise<RegisterResult> {
  try {
    const auth = await getUploadAuth();
    const body = new FormData();
    body.set("file", file);
    body.set("fileName", file.name);
    body.set("publicKey", auth.public_key);
    body.set("signature", auth.signature);
    body.set("expire", String(auth.expire));
    body.set("token", auth.token);
    const response = await fetch(auth.upload_url, { method: "POST", body });
    const uploaded: { fileId?: string; message?: string } = await response.json();
    if (!response.ok || !uploaded.fileId) {
      return { ok: false, error: uploaded.message ?? "ImageKit refused the upload." };
    }
    return await registerMedia(uploaded.fileId, altText);
  } catch {
    return { ok: false, error: "The upload failed. Check the connection and try again." };
  }
}
