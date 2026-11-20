"use server";

import { apiClient, unwrap } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { isDatabaseDown } from "@/lib/api/status";
import { clientIp } from "@/lib/request";

export type ContactValues = { name: string; email: string; subject: string; message: string };

export type ContactState =
  | { status: "idle" }
  | { status: "sent" }
  | { status: "failed"; error: string; fieldErrors: Record<string, string>; values: ContactValues };

function text(formData: FormData, name: string): string {
  return String(formData.get(name) ?? "").trim();
}

function failureMessage(error: unknown): string {
  if (isDatabaseDown(error)) {
    return "My database is offline right now, so the message can't be saved. Please try again in a few minutes.";
  }
  return error instanceof ApiError ? error.message : "Sending failed. Please try again.";
}

/**
 * Sends the contact form to the API with the visitor's IP (the API limits messages per IP).
 * `website` is the API's spam trap: people never see it, bots fill it in.
 */
export async function sendMessage(_state: ContactState, formData: FormData): Promise<ContactState> {
  const values: ContactValues = {
    name: text(formData, "name"),
    email: text(formData, "email"),
    subject: text(formData, "subject"),
    message: text(formData, "message"),
  };
  try {
    await unwrap(
      apiClient({ clientIp: await clientIp() }).POST("/contact", {
        body: { ...values, subject: values.subject || null, website: text(formData, "website") || null },
      }),
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 422) {
      return { status: "failed", error: "Please check the highlighted fields.", fieldErrors: error.fieldErrors(), values };
    }
    return { status: "failed", error: failureMessage(error), fieldErrors: {}, values };
  }
  return { status: "sent" };
}
