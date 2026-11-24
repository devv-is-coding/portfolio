/*
 * Admin forms are described as data: the same field list renders the form (client) and parses
 * the submitted FormData into the API body (server). Limits mirror the API's schemas, so the
 * browser catches most mistakes and the API's 422 answers land on the right field.
 */

type FieldBase = { name: string; label: string; hint?: string; required?: boolean };

export type Field =
  | (FieldBase & { kind: "text"; inputType?: "text" | "email" | "url"; maxLength?: number })
  | (FieldBase & { kind: "textarea"; maxLength?: number; rows?: number })
  | (FieldBase & { kind: "number"; min?: number; max?: number })
  | (FieldBase & { kind: "date" })
  | (FieldBase & { kind: "datetime" })
  | (FieldBase & { kind: "checkbox" })
  | (FieldBase & { kind: "select"; options: readonly { value: string; label: string }[] })
  | (FieldBase & {
      kind: "media";
      mediaKind: "image" | "document";
      /** Also offer uploading a new file, which joins the library and is chosen at once. */
      upload?: boolean;
    });

/** An item from the API as a form's starting values; only the fields' keys are read. */
export type FieldValues = Readonly<Record<string, unknown>>;

/**
 * The API body for a submitted form. Empty optional values become `null` (which clears them in
 * a PATCH); an empty number or date-time is left out, so the API's default applies (publishing
 * sets `published_at`, and clearing it while published is refused); a checkbox is a boolean.
 * Required text stays as typed, even empty, so the API's message lands on that field.
 */
export function parseFields(fields: readonly Field[], formData: FormData): Record<string, unknown> {
  const body: Record<string, unknown> = {};
  for (const field of fields) {
    const raw = formData.get(field.name);
    const value = typeof raw === "string" ? raw.trim() : "";
    switch (field.kind) {
      case "checkbox":
        body[field.name] = formData.has(field.name);
        break;
      case "number":
        if (value !== "") {
          body[field.name] = Number(value);
        }
        break;
      case "media":
        body[field.name] = value === "" ? null : Number(value);
        break;
      case "datetime":
        // <input type="datetime-local"> gives minutes; the API stores naive UTC seconds.
        if (value !== "") {
          body[field.name] = `${value}:00`;
        }
        break;
      default:
        body[field.name] = value === "" && !field.required ? null : value;
    }
  }
  return body;
}

/** The value an input shows for a value from the API. */
export function inputValue(field: Field, value: unknown): string {
  if (typeof value !== "string" && typeof value !== "number") {
    return "";
  }
  const text = String(value);
  return field.kind === "datetime" ? text.slice(0, 16) : text;
}
