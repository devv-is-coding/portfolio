"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { TextField } from "@/components/ui/fields";
import { mapWithConcurrency } from "@/lib/concurrency";
import { getUploadAuth, registerMedia } from "../_lib/actions";

// Files uploading at the same time: quicker than one by one, gentle on a phone connection.
const PARALLEL_UPLOADS = 3;

// `id` is the file's place in the selection: two files from different folders can share a name.
type Result = { id: number; name: string; error: string | null };
type Status =
  | { kind: "idle" }
  | { kind: "busy"; done: number; total: number }
  | { kind: "finished"; results: Result[] }
  | { kind: "failed"; error: string };

/**
 * Uploads one file straight from the browser to ImageKit with its own signature from the API
 * (ImageKit accepts each signature once; the file never passes through this server), then
 * registers it in the media library. Returns why it failed, or null.
 */
async function uploadFile(file: File, altText: string): Promise<string | null> {
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
      return uploaded.message ?? "ImageKit refused the upload.";
    }
    const result = await registerMedia(uploaded.fileId, altText);
    return result.ok ? null : result.error;
  } catch {
    return "The upload failed. Check the connection and try again.";
  }
}

/** Uploads one or more images or PDFs at once, showing how each one went. */
export function MediaUploader() {
  const router = useRouter();
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  async function upload(form: HTMLFormElement) {
    const data = new FormData(form);
    const files = data.getAll("file").filter((file): file is File => file instanceof File && file.size > 0);
    if (files.length === 0) {
      setStatus({ kind: "failed", error: "Choose at least one image or PDF first." });
      return;
    }
    const altText = String(data.get("alt_text") ?? "");
    let done = 0;
    setStatus({ kind: "busy", done, total: files.length });
    const results = await mapWithConcurrency(files, PARALLEL_UPLOADS, async (file, id) => {
      const error = await uploadFile(file, altText);
      done += 1;
      setStatus({ kind: "busy", done, total: files.length });
      return { id, name: file.name, error };
    });
    // Keep the selection only if everything failed, so it can be tried again as is.
    if (results.some((result) => result.error === null)) {
      form.reset();
      router.refresh();
    }
    setStatus({ kind: "finished", results });
  }

  const busy = status.kind === "busy";
  return (
    <form
      className="flex max-w-3xl flex-col gap-5 rounded-2xl border border-line p-5"
      onSubmit={(event) => {
        event.preventDefault();
        void upload(event.currentTarget);
      }}
    >
      {status.kind === "failed" && <Alert>{status.error}</Alert>}
      {status.kind === "finished" && <UploadSummary results={status.results} />}
      <div className="flex flex-col gap-2">
        <label htmlFor="media-file" className="text-sm font-semibold">
          Files
        </label>
        <input
          id="media-file"
          name="file"
          type="file"
          accept="image/*,application/pdf"
          multiple
          required
          className="text-sm file:mr-4 file:rounded-full file:border-0 file:bg-paper/10 file:px-4 file:py-2 file:text-paper"
        />
        <p className="text-sm text-muted">Images or PDF (a résumé). Choose several at once to upload them together.</p>
      </div>
      <TextField
        label="Alt text"
        name="alt_text"
        maxLength={255}
        hint="For images: what it shows. Used for every file chosen; change each one in the library below."
      />
      <Button type="submit" size="sm" disabled={busy} aria-busy={busy} className="self-start">
        {busy ? `Uploading ${status.done} of ${status.total}…` : "Upload"}
      </Button>
    </form>
  );
}

/** One line for everything that worked, and each failure with its reason. */
function UploadSummary({ results }: { results: Result[] }) {
  const uploaded = results.filter((result) => result.error === null);
  const failed = results.filter((result) => result.error !== null);
  return (
    <>
      {uploaded.length > 0 && (
        <Alert tone="success">
          {uploaded.length === 1
            ? `${uploaded[0]?.name} is in the library.`
            : `${uploaded.length} files are in the library.`}
        </Alert>
      )}
      {failed.length > 0 && (
        <Alert>
          <p>{failed.length === 1 ? "This file wasn't uploaded:" : `${failed.length} files weren't uploaded:`}</p>
          <ul className="mt-2 list-disc pl-5">
            {failed.map((result) => (
              <li key={result.id}>
                <span className="font-semibold">{result.name}</span>: {result.error}
              </li>
            ))}
          </ul>
        </Alert>
      )}
    </>
  );
}
