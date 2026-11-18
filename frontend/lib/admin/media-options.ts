import "server-only";
import { asAdmin } from "@/lib/auth/session";

export type MediaOptions = {
  image: { id: number; label: string }[];
  document: { id: number; label: string }[];
};

/** The media library as choices for media fields (newest first, up to 100 of each kind). */
export async function mediaOptions(): Promise<MediaOptions> {
  const list = (kind: "image" | "document") =>
    asAdmin((api) => api.GET("/admin/media", { params: { query: { kind, size: 100 } } }));
  const [images, documents] = await Promise.all([list("image"), list("document")]);
  const option = (item: (typeof images.items)[number]) => ({
    id: item.id,
    label: item.alt_text ? `${item.alt_text} (${item.file_path})` : item.file_path,
  });
  return { image: images.items.map(option), document: documents.items.map(option) };
}
