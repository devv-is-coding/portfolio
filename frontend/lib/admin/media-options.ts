import "server-only";
import { asAdmin } from "@/lib/auth/session";

/** A library file as a choice: its label for selects, its URL and size for thumbnails. */
export type MediaChoice = { id: number; label: string; url: string; width: number | null; height: number | null };

export type MediaOptions = {
  image: MediaChoice[];
  document: MediaChoice[];
};

/** The media library as choices for media fields (newest first, up to 100 of each kind). */
export async function mediaOptions(): Promise<MediaOptions> {
  const list = (kind: "image" | "document") =>
    asAdmin((api) => api.GET("/admin/media", { params: { query: { kind, size: 100 } } }));
  const [images, documents] = await Promise.all([list("image"), list("document")]);
  const option = (item: (typeof images.items)[number]): MediaChoice => ({
    id: item.id,
    label: item.alt_text ? `${item.alt_text} (${item.file_path})` : item.file_path,
    url: item.url,
    width: item.width,
    height: item.height,
  });
  return { image: images.items.map(option), document: documents.items.map(option) };
}
