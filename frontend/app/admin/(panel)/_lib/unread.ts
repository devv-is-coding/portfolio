"use server";

import { ApiError } from "@/lib/api/errors";
import { asAdmin } from "@/lib/auth/session";

/** How many contact messages are unread, for the dot in the admin menu; null if the API can't say. */
export async function unreadMessageCount(): Promise<number | null> {
  try {
    const page = await asAdmin((api) =>
      api.GET("/admin/contact-messages", { params: { query: { status: "unread", size: 1 } } }),
    );
    return page.total;
  } catch (error) {
    // A signed-out admin is sent to the login page by asAdmin; anything else only hides the dot.
    if (error instanceof ApiError) {
      return null;
    }
    throw error;
  }
}
