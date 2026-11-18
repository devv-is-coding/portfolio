"use client";

import { useActionState, useId } from "react";
import { Alert } from "@/components/ui/alert";
import { CheckboxField, SelectField, TextAreaField, TextField } from "@/components/ui/fields";
import { SubmitButton } from "@/components/ui/submit-button";
import { type Field, type FieldValues, inputValue } from "@/lib/admin/fields";
import { type FormAction, type FormState, IDLE } from "@/lib/admin/form-state";

export type MediaOption = { id: number; label: string };

type ResourceFormProps = {
  fields: readonly Field[];
  action: FormAction;
  /** The item's current values (edit); empty for a new one. */
  values?: FieldValues;
  /** The media library, for media fields. */
  media?: { image: readonly MediaOption[]; document: readonly MediaOption[] };
  submitLabel?: string;
};

/** A failed answer with what was typed: React resets a form after its action, even a failed one. */
type ShownState = FormState | (Extract<FormState, { status: "failed" }> & { submitted: FieldValues });

function snapshot(fields: readonly Field[], formData: FormData): FieldValues {
  return Object.fromEntries(
    fields.map((field) => [field.name, field.kind === "checkbox" ? formData.has(field.name) : String(formData.get(field.name) ?? "")]),
  );
}

/** An admin form built from its field list; shows the API's answer and field errors. */
export function ResourceForm({ fields, action, values = {}, media, submitLabel = "Save" }: ResourceFormProps) {
  const [state, formAction] = useActionState<ShownState, FormData>(async (previous, formData) => {
    const result = await action(previous, formData);
    return result.status === "failed" ? { ...result, submitted: snapshot(fields, formData) } : result;
  }, IDLE);
  const errors = state.status === "failed" ? state.fieldErrors : {};
  // After a refused save the form shows what was typed, not the stored values.
  const shown = "submitted" in state ? state.submitted : values;
  // Unique per form: a page can hold several (gallery images, social links, settings).
  const formId = useId();

  return (
    <form action={formAction} className="flex max-w-3xl flex-col gap-6">
      {state.status === "failed" && <Alert>{state.error}</Alert>}
      {state.status === "saved" && <Alert tone="success">{state.message}</Alert>}
      {fields.map((field) => {
        const common = {
          id: `${formId}-${field.name}`,
          label: field.label,
          name: field.name,
          hint: field.hint,
          error: errors[field.name],
          required: field.required,
        };
        const value = shown[field.name];
        switch (field.kind) {
          case "textarea":
            return (
              <TextAreaField
                key={field.name}
                {...common}
                maxLength={field.maxLength}
                rows={field.rows ?? 6}
                defaultValue={inputValue(field, value)}
              />
            );
          case "checkbox":
            return <CheckboxField key={field.name} {...common} defaultChecked={value === true} />;
          case "select":
            return (
              <SelectField key={field.name} {...common} defaultValue={inputValue(field, value)}>
                {!field.required && <option value="">None</option>}
                {field.options.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </SelectField>
            );
          case "media":
            return (
              <SelectField key={field.name} {...common} defaultValue={inputValue(field, value)}>
                <option value="">None</option>
                {(media?.[field.mediaKind] ?? []).map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </SelectField>
            );
          default:
            return (
              <TextField
                key={field.name}
                {...common}
                type={
                  field.kind === "text"
                    ? (field.inputType ?? "text")
                    : field.kind === "datetime"
                      ? "datetime-local"
                      : field.kind
                }
                maxLength={field.kind === "text" ? field.maxLength : undefined}
                min={field.kind === "number" ? field.min : undefined}
                max={field.kind === "number" ? field.max : undefined}
                defaultValue={inputValue(field, value)}
              />
            );
        }
      })}
      <SubmitButton pendingLabel="Saving…" className="self-start">
        {submitLabel}
      </SubmitButton>
    </form>
  );
}
