"use client";

import { type ReactNode, useActionState } from "react";
import { Alert } from "@/components/ui/alert";
import { SubmitButton } from "@/components/ui/submit-button";
import { type FormAction, IDLE } from "@/lib/admin/form-state";

type GalleryPickerProps = {
  action: FormAction;
  /** The pictures to choose from: checkboxes named `ids`, rendered on the server. */
  children: ReactNode;
};

/** Adds every ticked picture to the gallery in one go, and says how it went. */
export function GalleryPicker({ action, children }: GalleryPickerProps) {
  const [state, formAction] = useActionState(action, IDLE);
  return (
    <form action={formAction} className="flex flex-col gap-5">
      {state.status === "failed" && <Alert>{state.error}</Alert>}
      {state.status === "saved" && <Alert tone="success">{state.message}</Alert>}
      <fieldset>
        <legend className="mb-3 text-sm text-muted">Tick every picture to add; they go to the end, in this order.</legend>
        {children}
      </fieldset>
      <SubmitButton size="sm" pendingLabel="Adding…" className="self-start">
        Add selected pictures
      </SubmitButton>
    </form>
  );
}
