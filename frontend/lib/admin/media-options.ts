import "server-only";
import type { components } from "@/lib/api/schema";
import { asAdmin } from "@/lib/auth/session";

/** A library file as a choice: its label for selects, its URL and size for thumbnails. */
export type MediaChoice = { id: number; label: string; url: string; width: number | null; height: number | null };

export type MediaOptions = {
  image: MediaChoice[];
  document: MediaChoice[];
};

export function toMediaChoice(item: components["schemas"]["MediaRead"]): MediaChoice {
  return {
    id: item.id,
    label: item.alt_text ? `${item.alt_text} (${item.file_path})` : item.file_path,
    url: item.url,
    width: item.width,
    height: item.height,
  };
}

/** The media library as choices for media fields (newest first, up to 100 of each kind). */
export async function mediaOptions(): Promise<MediaOptions> {
  const list = (kind: "image" | "document") =>
    asAdmin((api) => api.GET("/admin/media", { params: { query: { kind, size: 100 } } }));
  const [images, documents] = await Promise.all([list("image"), list("document")]);
  return { image: images.items.map(toMediaChoice), document: documents.items.map(toMediaChoice) };
}
