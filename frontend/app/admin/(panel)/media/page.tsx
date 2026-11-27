import type { Metadata } from "next";
import { PageHeader } from "@/components/admin/admin-ui";
import { DeleteButton } from "@/components/admin/delete-button";
import { ListPagination } from "@/components/admin/list-pagination";
import { ResourceForm } from "@/components/admin/resource-form";
import { MediaImage } from "@/components/media-image";
import { EmptyState } from "@/components/ui/empty-state";
import { ADMIN_PAGE_SIZE, keepPageInRange } from "@/lib/admin/list-pages";
import { asAdmin } from "@/lib/auth/session";
import { pageParam } from "@/lib/search-params";
import { MediaDialog } from "./_components/media-dialog";
import { MediaUploader } from "./_components/media-uploader";
import { deleteMedia, saveMediaAlt } from "./_lib/actions";
import { MEDIA_FIELDS } from "./_lib/fields";

// Session-gated: blocks on the server (see the panel layout).
export const instant = false;

export const metadata: Metadata = { title: "Media" };

const KB = 1024;

function fileSize(bytes: number): string {
  return bytes < KB * KB ? `${Math.round(bytes / KB)} KB` : `${(bytes / KB / KB).toFixed(1)} MB`;
}

/** The file name without ImageKit's leading slash. */
function fileName(path: string): string {
  return path.replace(/^\//, "");
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
      <section className="mt-12 flex flex-col gap-4" aria-labelledby="files-heading">
        <div className="flex items-baseline justify-between gap-4">
          <h2 id="files-heading" className="font-display text-2xl">
            Files
          </h2>
          {list.total > 0 && <p className="text-sm text-muted">{list.total} in the library · hover to preview, click to open</p>}
        </div>
        {items.length === 0 ? (
          <EmptyState title="No files yet">Upload an image or a PDF above.</EmptyState>
        ) : (
          <ul className="divide-y divide-line rounded-card border border-line">
            {items.map((item) => {
              const name = item.alt_text ?? "No alt text";
              const details = [
                item.kind === "image" ? "Image" : "PDF",
                fileSize(item.size_bytes),
                item.width && item.height ? `${item.width}×${item.height}` : null,
              ]
                .filter(Boolean)
                .join(" · ");
              return (
                <li key={item.id}>
                  <MediaDialog
                    title={name}
                    row={
                      <>
                        <span className={item.alt_text ? "truncate font-semibold" : "truncate text-muted italic"}>{name}</span>
                        <span className="truncate font-mono text-xs text-muted">{fileName(item.file_path)}</span>
                        <span className="font-mono text-xs text-muted sm:text-right">{details}</span>
                      </>
                    }
                    preview={
                      item.kind === "image" ? (
                        <MediaImage
                          src={item.url}
                          alt=""
                          width={item.width}
                          height={item.height}
                          sizes="224px"
                          loading="lazy"
                          className="h-auto max-h-56 w-full rounded-lg object-contain"
                        />
                      ) : undefined
                    }
                  >
                    {item.kind === "image" ? (
                      <MediaImage
                        src={item.url}
                        alt={item.alt_text ?? ""}
                        width={item.width}
                        height={item.height}
                        sizes="(min-width: 1024px) 960px, 100vw"
                        loading="lazy"
                        className="mx-auto h-auto max-h-[55svh] w-auto max-w-full rounded-lg bg-ink-raised object-contain"
                      />
                    ) : (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex h-48 items-center justify-center rounded-lg bg-ink-raised font-display text-4xl text-muted hover:text-accent"
                      >
                        Open PDF ↗
                      </a>
                    )}
                    <p className="font-mono text-xs break-all text-muted">
                      {fileName(item.file_path)} · {item.mime_type} · {details}
                      {" · "}
                      <a href={item.url} target="_blank" rel="noopener noreferrer" className="underline hover:text-accent">
                        original ↗
                      </a>
                    </p>
                    <ResourceForm
                      fields={MEDIA_FIELDS}
                      action={saveMediaAlt.bind(null, item.id)}
                      values={item}
                      submitLabel="Save alt text"
                    />
                    <DeleteButton action={deleteMedia.bind(null, item.id)} what={`${fileName(item.file_path)} (pages using it lose it)`} />
                  </MediaDialog>
                </li>
              );
            })}
          </ul>
        )}
        <ListPagination path="/admin/media" list={list} />
      </section>
    </>
  );
}
