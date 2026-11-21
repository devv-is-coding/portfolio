import type { Metadata } from "next";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/admin/admin-ui";
import { DeleteButton } from "@/components/admin/delete-button";
import { ResourceForm } from "@/components/admin/resource-form";
import { MediaImage } from "@/components/media-image";
import { asAdmin } from "@/lib/auth/session";
import { MediaUploader } from "./_components/media-uploader";
import { deleteMedia, saveMediaAlt } from "./_lib/actions";
import { MEDIA_FIELDS } from "./_lib/fields";
import { ListPagination } from "@/components/admin/list-pagination";
import { ADMIN_PAGE_SIZE, keepPageInRange } from "@/lib/admin/list-pages";
import { pageParam } from "@/lib/search-params";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Media" };

const KB = 1024;

function fileSize(bytes: number): string {
  return bytes < KB * KB ? `${Math.round(bytes / KB)} KB` : `${(bytes / KB / KB).toFixed(1)} MB`;
}

export default async function MediaPage({ searchParams }: PageProps<"/admin/media">) {
  const page = pageParam((await searchParams).page);
  const list = await asAdmin((api) => api.GET("/admin/media", { params: { query: { page, size: ADMIN_PAGE_SIZE } } }));
  keepPageInRange(list, "/admin/media");
  const { items } = list;

  return (
    <>
      <PageHeader eyebrow="Library" title="Media" />
      <MediaUploader />
      <section className="mt-12 flex flex-col gap-6" aria-label="Files">
        {items.length === 0 && <EmptyState title="No files yet">Upload an image or a PDF above.</EmptyState>}
        <div className="grid gap-6 lg:grid-cols-2">
          {items.map((item) => (
            <article key={item.id} className="flex flex-col gap-4 rounded-2xl border border-line p-5">
              {item.kind === "image" ? (
                <MediaImage
                  src={item.url}
                  alt={item.alt_text ?? ""}
                  width={item.width}
                  height={item.height}
                  sizes="(min-width: 1024px) 400px, 100vw"
                  className="h-48 w-full rounded-lg bg-ink object-contain"
                />
              ) : (
                <a href={item.url} target="_blank" rel="noopener noreferrer" className="flex h-48 items-center justify-center rounded-lg bg-ink font-display text-4xl font-extrabold text-muted hover:text-accent">
                  PDF ↗
                </a>
              )}
              <p className="font-mono text-xs break-all text-muted">
                {item.file_path} · {item.mime_type} · {fileSize(item.size_bytes)}
                {item.width && item.height ? ` · ${item.width}×${item.height}` : ""}
              </p>
              <ResourceForm fields={MEDIA_FIELDS} action={saveMediaAlt.bind(null, item.id)} values={item} submitLabel="Save alt text" />
              <DeleteButton action={deleteMedia.bind(null, item.id)} what={`${item.file_path} (pages using it lose it)`} />
            </article>
          ))}
        </div>
        <ListPagination path="/admin/media" list={list} />
      </section>
    </>
  );
}
