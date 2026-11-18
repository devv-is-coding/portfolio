"use client";

import { useActionState } from "react";
import { Alert } from "@/components/ui/alert";
import { TextAreaField, TextField } from "@/components/ui/fields";
import { SubmitButton } from "@/components/ui/submit-button";
import { type ContactState, sendMessage } from "../_lib/actions";

// Limits from the API (ContactMessageCreate), so the browser catches them first.
const MAX = { name: 150, email: 255, subject: 255, message: 5000 } as const;

export function ContactForm() {
  const [state, action] = useActionState<ContactState, FormData>(sendMessage, { status: "idle" });

  if (state.status === "sent") {
    return (
      <Alert tone="success" className="text-base">
        <p className="font-semibold">Thanks, your message is on its way.</p>
        <p className="mt-1 text-muted">I read every message and reply as soon as I can.</p>
      </Alert>
    );
  }

  const failed = state.status === "failed" ? state : undefined;
  const errors = failed?.fieldErrors ?? {};

  return (
    <form action={action} className="flex flex-col gap-6">
      {failed && <Alert>{failed.error}</Alert>}
      <div className="grid gap-6 sm:grid-cols-2">
        <TextField label="Name" name="name" autoComplete="name" required maxLength={MAX.name} defaultValue={failed?.values.name} error={errors.name} />
        <TextField label="Email" name="email" type="email" autoComplete="email" required maxLength={MAX.email} defaultValue={failed?.values.email} error={errors.email} />
      </div>
      <TextField label="Subject" name="subject" maxLength={MAX.subject} hint="Optional" defaultValue={failed?.values.subject} error={errors.subject} />
      <TextAreaField label="Message" name="message" required maxLength={MAX.message} defaultValue={failed?.values.message} error={errors.message} />
      {/* Spam trap: hidden from people and screen readers, filled in by bots. */}
      <div aria-hidden="true" className="absolute -left-[9999px] h-px w-px overflow-hidden">
        <label htmlFor="field-website">Leave this empty</label>
        <input id="field-website" name="website" type="text" tabIndex={-1} autoComplete="off" />
      </div>
      <SubmitButton pendingLabel="Sending…" className="self-start">
        Send message
      </SubmitButton>
    </form>
  );
}
