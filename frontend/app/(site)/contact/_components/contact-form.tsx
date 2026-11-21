"use client";

import { useActionState, useEffect, useRef, useState } from "react";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { TextAreaField, TextField } from "@/components/ui/fields";
import { SubmitButton } from "@/components/ui/submit-button";
import { type ContactState, sendMessage } from "../_lib/actions";

// Limits from the API (ContactMessageCreate), so the browser catches them first.
const MAX = { name: 150, email: 255, subject: 255, message: 5000 } as const;

/** The contact form; after a message is sent, a confirmation with a way to write another. */
export function ContactForm() {
  // A new key starts a fresh form (empty fields, no state) for "Send another message".
  const [round, setRound] = useState(0);
  return <MessageForm key={round} onSendAnother={() => setRound((n) => n + 1)} />;
}

/**
 * Shown in place of the form once the message is saved. It takes focus, so it's scrolled into
 * view and read out by screen readers, and the visitor can't miss that it worked.
 */
function SentConfirmation({ onSendAnother }: { onSendAnother: () => void }) {
  const panel = useRef<HTMLDivElement>(null);
  useEffect(() => {
    panel.current?.focus();
  }, []);
  return (
    <div
      ref={panel}
      tabIndex={-1}
      role="status"
      className="flex flex-col items-start gap-4 rounded-2xl border border-accent/50 bg-accent/10 p-6 outline-none sm:p-8"
    >
      <span aria-hidden="true" className="flex size-12 items-center justify-center rounded-full bg-accent text-2xl font-extrabold text-accent-ink">
        ✓
      </span>
      <h2 className="font-display text-2xl font-extrabold">Message sent</h2>
      <p className="text-muted">
        Thanks for reaching out. Your message arrived safely; I read every one and reply to the email you gave as soon as I can.
      </p>
      <Button type="button" variant="outline" size="sm" onClick={onSendAnother}>
        Send another message
      </Button>
    </div>
  );
}

function MessageForm({ onSendAnother }: { onSendAnother: () => void }) {
  const [state, action] = useActionState<ContactState, FormData>(sendMessage, { status: "idle" });

  if (state.status === "sent") {
    return <SentConfirmation onSendAnother={onSendAnother} />;
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
