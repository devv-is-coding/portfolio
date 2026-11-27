"use client";

import { useRef, useState } from "react";
import { MediaImage } from "@/components/media-image";
import { Button } from "@/components/ui/button";
import { SelectField } from "@/components/ui/fields";
import type { MediaChoice } from "@/lib/admin/media-options";
import { uploadMedia } from "@/lib/admin/upload-media";

type MediaFieldProps = {
  id: string;
  name: string;
  label: string;
  hint?: string;
  error?: string;
  required?: boolean;
  defaultValue: string;
  mediaKind: "image" | "document";
  options: readonly MediaChoice[];
};

type Upload = { kind: "idle" } | { kind: "busy" } | { kind: "done"; name: string } | { kind: "failed"; error: string };

/**
 * A media field that also takes a new file: it is uploaded to the library and chosen in the
 * list, so saving the form uses it. The chosen image is previewed under the list.
 */
export function MediaField({ defaultValue, mediaKind, options, ...field }: MediaFieldProps) {
  const [choices, setChoices] = useState(options);
  const [value, setValue] = useState(defaultValue);
  const [upload, setUpload] = useState<Upload>({ kind: "idle" });
  const fileInput = useRef<HTMLInputElement>(null);
  const chosen = choices.find((choice) => String(choice.id) === value);
  const what = mediaKind === "image" ? "picture" : "PDF";

  async function uploadChosenFile(input: HTMLInputElement) {
    const file = input.files?.[0];
    if (!file) {
      return;
    }
    setUpload({ kind: "busy" });
    const result = await uploadMedia(file, "");
    // The input has no name, so the file itself is never part of the form.
    input.value = "";
    if (!result.ok) {
      setUpload({ kind: "failed", error: result.error });
      return;
    }
    setChoices((current) => [result.media, ...current]);
    setValue(String(result.media.id));
    setUpload({ kind: "done", name: file.name });
  }

  const busy = upload.kind === "busy";
  return (
    <div className="flex flex-col gap-3">
      <SelectField {...field} value={value} onChange={(event) => setValue(event.target.value)}>
        <option value="">None</option>
        {choices.map((choice) => (
          <option key={choice.id} value={choice.id}>
            {choice.label}
          </option>
        ))}
      </SelectField>
      <div className="flex flex-wrap items-center gap-3">
        <input
          ref={fileInput}
          type="file"
          accept={mediaKind === "image" ? "image/*" : "application/pdf"}
          className="sr-only"
          tabIndex={-1}
          aria-hidden="true"
          onChange={(event) => void uploadChosenFile(event.currentTarget)}
        />
        <Button variant="secondary" size="sm" disabled={busy} aria-busy={busy} onClick={() => fileInput.current?.click()}>
          {busy ? "Uploading…" : `Upload a new ${what}`}
        </Button>
        <p role="status" className={upload.kind === "failed" ? "text-sm text-signal" : "text-sm text-muted"}>
          {upload.kind === "done" && `${upload.name} is uploaded and chosen. Save to keep it.`}
          {upload.kind === "failed" && `The upload didn't work: ${upload.error}`}
        </p>
      </div>
      {mediaKind === "image" && chosen && (
        <MediaImage
          src={chosen.url}
          alt=""
          width={chosen.width}
          height={chosen.height}
          sizes="320px"
          loading="lazy"
          className="h-auto max-h-60 w-auto max-w-xs rounded-lg border border-line bg-ink-raised object-contain"
        />
      )}
    </div>
  );
}
