"use client";

import { SubmitButton } from "@/components/ui/submit-button";

type DeleteButtonProps = {
  action: () => Promise<void>;
  /** What is deleted, for the confirmation: "the skill FastAPI". */
  what: string;
  label?: string;
};

/** Deletes after the browser's confirmation dialog; a cancel sends nothing. */
export function DeleteButton({ action, what, label = "Delete" }: DeleteButtonProps) {
  return (
    <form
      action={action}
      onSubmit={(event) => {
        if (!window.confirm(`Delete ${what}? This can't be undone.`)) {
          event.preventDefault();
        }
      }}
    >
      <SubmitButton variant="danger" size="sm" pendingLabel="Deleting…">
        {label}
      </SubmitButton>
    </form>
  );
}
