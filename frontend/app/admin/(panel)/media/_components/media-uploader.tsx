"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { TextField } from "@/components/ui/fields";
import { getUploadAuth, registerMedia } from "../_lib/actions";

type Status = { kind: "idle" } | { kind: "busy"; step: string } | { kind: "done"; name: string } | { kind: "failed"; error: string };

/**
 * Uploads straight from the browser to ImageKit with a signature from the API (the file never
 * passes through this server), then registers it in the media library.
 */
export function MediaUploader() {
  const router = useRouter();
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  async function upload(form: HTMLFormElement) {
    const data = new FormData(form);
    const file = data.get("file");
    if (!(file instanceof File) || file.size === 0) {
      setStatus({ kind: "failed", error: "Choose an image or a PDF first." });
      return;
    }
    try {
      setStatus({ kind: "busy", step: "Uploading…" });
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
        setStatus({ kind: "failed", error: uploaded.message ?? "ImageKit refused the upload." });
        return;
      }
      setStatus({ kind: "busy", step: "Adding to the library…" });
      const result = await registerMedia(uploaded.fileId, String(data.get("alt_text") ?? ""));
      if (!result.ok) {
        setStatus({ kind: "failed", error: result.error });
        return;
      }
      form.reset();
      setStatus({ kind: "done", name: file.name });
      router.refresh();
    } catch {
      setStatus({ kind: "failed", error: "The upload failed. Check the connection and try again." });
    }
  }

  return (
    <form
      className="flex max-w-3xl flex-col gap-5 rounded-2xl border border-line p-5"
      onSubmit={(event) => {
        event.preventDefault();
        void upload(event.currentTarget);
      }}
    >
      {status.kind === "failed" && <Alert>{status.error}</Alert>}
      {status.kind === "done" && <Alert tone="success">{status.name} is in the library.</Alert>}
      <div className="flex flex-col gap-2">
        <label htmlFor="media-file" className="text-sm font-semibold">
          File
        </label>
        <input
          id="media-file"
          name="file"
          type="file"
          accept="image/*,application/pdf"
          required
          className="text-sm file:mr-4 file:rounded-full file:border-0 file:bg-paper/10 file:px-4 file:py-2 file:text-paper"
        />
        <p className="text-sm text-muted">Images or PDF (a résumé).</p>
      </div>
      <TextField label="Alt text" name="alt_text" maxLength={255} hint="For images: what it shows." />
      <Button type="submit" size="sm" disabled={status.kind === "busy"} aria-busy={status.kind === "busy"} className="self-start">
        {status.kind === "busy" ? status.step : "Upload"}
      </Button>
    </form>
  );
}
