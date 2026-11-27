"use client";

import { type ReactNode, useRef } from "react";
import { Button } from "@/components/ui/button";

type CertificateViewerProps = {
  /** The certification's name: the dialog's heading. */
  title: string;
  /** The certificate picture, rendered on the server; it loads only when the dialog opens. */
  children: ReactNode;
};

/**
 * "View certificate": the picture in a modal (the browser's own <dialog>: Escape closes it,
 * focus stays inside, and a click beside the picture closes it too).
 */
export function CertificateViewer({ title, children }: CertificateViewerProps) {
  const dialog = useRef<HTMLDialogElement>(null);
  return (
    <>
      <Button variant="secondary" size="sm" aria-haspopup="dialog" onClick={() => dialog.current?.showModal()}>
        View certificate
      </Button>
      <dialog
        ref={dialog}
        aria-label={title}
        onClick={(event) => {
          if (event.target === event.currentTarget) {
            event.currentTarget.close();
          }
        }}
        className="m-auto max-h-[94svh] w-[min(72rem,calc(100vw-1.5rem))] overflow-y-auto rounded-card border border-line bg-ink p-0 text-paper backdrop:bg-ink/90 backdrop:backdrop-blur-sm"
      >
        <div className="flex flex-col gap-4 p-4 sm:p-6">
          <div className="flex items-start justify-between gap-4">
            <h2 className="font-display text-xl sm:text-2xl">{title}</h2>
            <button
              type="button"
              onClick={() => dialog.current?.close()}
              className="shrink-0 rounded-btn border border-line px-4 py-1.5 text-sm hover:border-paper pointer-coarse:min-h-11"
            >
              Close
            </button>
          </div>
          {children}
        </div>
      </dialog>
    </>
  );
}
