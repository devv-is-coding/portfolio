"use client";

import { useActionState } from "react";
import { Alert } from "@/components/ui/alert";
import { SubmitButton } from "@/components/ui/submit-button";
import { type FormAction, IDLE } from "@/lib/admin/form-state";

type ChecklistFormProps = {
  legend: string;
  options: readonly { id: number; label: string }[];
  /** The ids checked now. */
  selected: readonly number[];
  action: FormAction;
  submitLabel: string;
  empty: string;
};

/** Picks a set of items (a project's skills, a post's tags); sends the checked ids as `ids`. */
export function ChecklistForm({ legend, options, selected, action, submitLabel, empty }: ChecklistFormProps) {
  const [state, formAction] = useActionState(action, IDLE);
  if (options.length === 0) {
    return <p className="text-muted">{empty}</p>;
  }
  return (
    <form action={formAction} className="flex flex-col gap-6">
      {state.status === "failed" && <Alert>{state.error}</Alert>}
      {state.status === "saved" && <Alert tone="success">{state.message}</Alert>}
      <fieldset>
        <legend className="sr-only">{legend}</legend>
        <div className="flex flex-wrap gap-2">
          {options.map((option) => (
            <label
              key={option.id}
              className="flex cursor-pointer items-center gap-2 rounded-btn border border-line px-3 py-1.5 text-sm has-checked:border-accent has-checked:text-accent"
            >
              <input type="checkbox" name="ids" value={option.id} defaultChecked={selected.includes(option.id)} className="accent-accent" />
              {option.label}
            </label>
          ))}
        </div>
      </fieldset>
      <SubmitButton size="sm" pendingLabel="Saving…" className="self-start">
        {submitLabel}
      </SubmitButton>
    </form>
  );
}
