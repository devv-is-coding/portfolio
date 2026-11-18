/** What an admin form's Server Action answers; the form shows it. */
export type FormState =
  | { status: "idle" }
  | { status: "saved"; message: string }
  | { status: "failed"; error: string; fieldErrors: Record<string, string> };

export const IDLE: FormState = { status: "idle" };

export type FormAction = (state: FormState, formData: FormData) => Promise<FormState>;
