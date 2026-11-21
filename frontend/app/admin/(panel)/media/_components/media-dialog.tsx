"use client";

import { type ReactNode, useRef } from "react";

type MediaDialogProps = {
  /** The row: what the button shows (name, file, details). */
  row: ReactNode;
  /** A small preview shown while the row is hovered or focused (images only). */
  preview?: ReactNode;
  /** The dialog's heading, for screen readers and the top of the dialog. */
  title: string;
  /** The expanded view: the full picture, its details and its forms. */
  children: ReactNode;
};

/**
 * One file in the media list: hovering shows a small preview, clicking opens the full view in
 * a modal (the browser's own <dialog>: Escape closes it, focus stays inside). Images inside
 * load only when shown, so a long list costs nothing until it's looked at.
 */
export function MediaDialog({ row, preview, title, children }: MediaDialogProps) {
  const dialog = useRef<HTMLDialogElement>(null);
  return (
    <>
      <button
        type="button"
        aria-haspopup="dialog"
        onClick={() => dialog.current?.showModal()}
        className="group relative grid w-full gap-1 px-4 py-3 text-left hover:bg-ink-raised focus-visible:bg-ink-raised sm:grid-cols-[minmax(0,2fr)_minmax(0,2fr)_auto] sm:items-center sm:gap-4"
      >
        {row}
        {preview && (
          <span
            aria-hidden="true"
            className="pointer-events-none absolute top-full left-4 z-20 mt-1 hidden w-56 rounded-xl border border-line bg-ink-raised p-1.5 shadow-2xl shadow-ink group-hover:block group-focus-visible:block"
          >
            {preview}
          </span>
        )}
      </button>
      <dialog
        ref={dialog}
        aria-label={title}
        // A click on the backdrop lands on the <dialog> itself: close, like Escape.
        onClick={(event) => {
          if (event.target === event.currentTarget) {
            event.currentTarget.close();
          }
        }}
        className="m-auto max-h-[92svh] overflow-y-auto w-[min(64rem,calc(100vw-2rem))] rounded-2xl border border-line bg-ink p-0 text-paper backdrop:bg-ink/85 backdrop:backdrop-blur-sm"
      >
        <div className="flex flex-col gap-6 p-5 sm:p-6">
          <div className="flex items-start justify-between gap-4">
            <h2 className="font-display text-xl font-extrabold break-all">{title}</h2>
            <button
              type="button"
              onClick={() => dialog.current?.close()}
              className="shrink-0 rounded-full border border-line px-3 py-1 text-sm hover:border-paper"
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
